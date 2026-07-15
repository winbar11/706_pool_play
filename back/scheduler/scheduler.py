import logging
import unicodedata

from sqlalchemy import select, update
from database.db import get_session, to_dict
from database.models import Golfer, Team, TournamentSetting
from clients.espn_client import fetch_leaderboard, parse_leaderboard
from scoring.scoring import calc_all_team_scores

logger = logging.getLogger(__name__)

_CHAR_MAP = str.maketrans("øØðÐłŁ", "oOdDlL")

def normalize_name(name: str) -> str:
    """Strip accents/diacritics for fuzzy matching.
    NFD decomposition handles å→a, é→e, etc.
    The char map handles non-decomposing letters like ø, ð, ł.
    """
    name = name.translate(_CHAR_MAP)
    return ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def _unique_match(session, stmt, stage: str, player_name: str):
    """Return the golfer matched by stmt only if exactly one row matches.

    Silently picking .first() among ambiguous matches (e.g. two golfers whose
    names both contain a common substring) risks attributing one golfer's
    score to another, which corrupts a real-money payout with no visibility.
    Ambiguous or zero matches are logged loudly and skipped instead.
    """
    rows = session.execute(stmt).scalars().all()
    if len(rows) == 1:
        return rows[0]
    if len(rows) > 1:
        candidates = ", ".join(f"{g.id}:{g.name}" for g in rows)
        logger.error(
            f"Ambiguous {stage} match for ESPN player '{player_name}' — "
            f"{len(rows)} candidates ({candidates}). Skipping this update to "
            "avoid mis-attributing a score."
        )
    return None


async def refresh_scores():
    logger.info("=== Starting score refresh ===")
    try:
        lb_data = await fetch_leaderboard()
        if not lb_data:
            logger.warning("No leaderboard data returned from ESPN")
            return

        players = parse_leaderboard(lb_data)
        if not players:
            logger.warning("No players parsed")
            return

        logger.info(f"Processing {len(players)} players from ESPN")
        matched = 0

        with get_session() as session:
            # ── Step 1: Update each golfer's scores ──
            for player in players:
                espn_id = player["espn_id"]
                name    = player["name"]

                # Try ESPN ID first
                golfer = _unique_match(
                    session, select(Golfer).where(Golfer.espn_id.like(f"{espn_id}%")),
                    "espn_id", name,
                )

                # Try exact name
                if not golfer:
                    golfer = _unique_match(
                        session, select(Golfer).where(Golfer.name.like(f"%{name}%")),
                        "name", name,
                    )

                # Try normalized name (strips accents like ø, é, å)
                if not golfer:
                    normalized = normalize_name(name)
                    golfer = _unique_match(
                        session, select(Golfer).where(Golfer.name.ilike(f"%{normalized}%")),
                        "normalized-name", name,
                    )

                if not golfer:
                    logger.debug(f"No DB match for: {name}")
                    continue

                matched += 1
                current_round = player.get("current_round", 0)

                updates = {
                            "current_round":   current_round,
                            "total_score":     player.get("total_score"),
                            "made_cut":        player.get("made_cut", 1),
                        }
                # Only update finish_position if it's a real value
                finish_pos = player.get("finish_position")
                if finish_pos is not None and finish_pos > 0:
                    updates["finish_position"] = finish_pos

                in_progress = player.get("in_progress", False)
                for r in range(1, 5):
                    rs = player.get(f"round{r}_score")
                    if rs is not None:
                        updates[f"round{r}_score"] = rs
                    elif in_progress and r == current_round:
                        # Player is mid-round — clear any stale partial stroke count
                        updates[f"round{r}_score"] = None

                for k, v in updates.items():
                    setattr(golfer, k, v)

            logger.info(f"Matched and updated {matched}/{len(players)} players")

            # ── Step 2: Determine solo leaders after each round ──
            session.execute(update(Golfer).values(
                solo_leader_r1=0, solo_leader_r2=0,
                solo_leader_r3=0, solo_leader_r4=0,
            ))

            for round_num in range(1, 5):
                round_col = getattr(Golfer, f"round{round_num}_score")
                top = session.execute(
                    select(Golfer.id, Golfer.total_score)
                    .where(round_col.isnot(None), Golfer.current_round >= round_num)
                    .order_by(Golfer.total_score.asc())
                    .limit(2)
                ).all()

                if not top:
                    continue

                if len(top) == 1 or top[0].total_score < top[1].total_score:
                    leader_id = top[0].id
                    session.execute(
                        update(Golfer).where(Golfer.id == leader_id)
                        .values(**{f"solo_leader_r{round_num}": 1})
                    )
                    logger.info(f"Round {round_num} solo leader: id={leader_id} at {top[0].total_score}")
                else:
                    logger.info(f"Round {round_num}: tie at {top[0].total_score} — no solo leader bonus")

            # ── Step 3: Recalculate all team scores ──
            teams = session.query(Team).all()
            all_teams = [
                {**to_dict(team), "golfers": [to_dict(g) for g in team.golfers]}
                for team in teams
            ]

            tc_row = session.get(TournamentSetting, "tournament_complete")
            tournament_complete = tc_row is not None and tc_row.value == "1"

            all_golfers = [to_dict(g) for g in session.query(Golfer).all()]

            scores = calc_all_team_scores(all_teams, tournament_complete, all_golfers)

            for team_id, result in scores.items():
                logger.info(
                    f"Team {team_id}: raw={result['raw']} "
                    f"bonus={result['bonus']} final={result['final']}"
                )
                team = session.get(Team, team_id)
                team.final_score = result["final"]
                team.bonus_shots = result["bonus"]
                team.dk_total_points = result["final"]

        logger.info("=== Score refresh complete ===")

    except Exception as e:
        logger.error(f"Score refresh failed: {e}", exc_info=True)
