import asyncio
import logging
import unicodedata
from database.db import get_conn
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
        conn = get_conn()
        cur  = conn.cursor()
        matched = 0

        # ── Step 1: Update each golfer's scores ──
        for player in players:
            espn_id = player["espn_id"]
            name    = player["name"]

            # Try ESPN ID first
            cur.execute("SELECT * FROM golfers WHERE espn_id LIKE %s", (f"{espn_id}%",))
            row = cur.fetchone()

            # Try exact name
            if not row:
                cur.execute("SELECT * FROM golfers WHERE name LIKE %s", (f"%{name}%",))
                row = cur.fetchone()

            # Try normalized name (strips accents like ø, é, å)
            if not row:
                normalized = normalize_name(name)
                cur.execute(
                    "SELECT * FROM golfers WHERE LOWER(name) LIKE %s",
                    (f"%{normalized}%",)
                )
                row = cur.fetchone()

            if not row:
                logger.debug(f"No DB match for: {name}")
                continue

            matched += 1
            golfer        = dict(row)
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

            for r in range(1, 5):
                rs = player.get(f"round{r}_score")
                if rs is not None:
                    updates[f"round{r}_score"] = rs

            set_clause = ", ".join(f"{k}=%s" for k in updates)
            cur.execute(
                f"UPDATE golfers SET {set_clause} WHERE id=%s",
                (*updates.values(), golfer["id"])
            )

        logger.info(f"Matched and updated {matched}/{len(players)} players")

        # ── Step 2: Determine solo leaders after each round ──
        cur.execute("""
            UPDATE golfers SET
                solo_leader_r1=0, solo_leader_r2=0,
                solo_leader_r3=0, solo_leader_r4=0
        """)

        for round_num in range(1, 5):
            cur.execute(f"""
                SELECT id, total_score
                FROM golfers
                WHERE round{round_num}_score IS NOT NULL
                AND current_round >= %s
                ORDER BY total_score ASC
                LIMIT 2
            """, (round_num,))
            top = cur.fetchall()

            if not top:
                continue

            if len(top) == 1 or top[0]["total_score"] < top[1]["total_score"]:
                leader_id = top[0]["id"]
                cur.execute(
                    f"UPDATE golfers SET solo_leader_r{round_num}=1 WHERE id=%s",
                    (leader_id,)
                )
                logger.info(f"Round {round_num} solo leader: id={leader_id} at {top[0]['total_score']}")
            else:
                logger.info(f"Round {round_num}: tie at {top[0]['total_score']} — no solo leader bonus")

        # ── Step 3: Recalculate all team scores ──
        cur.execute("""
            SELECT t.*, u.username FROM teams t
            JOIN users u ON u.id = t.user_id
        """)
        teams_raw = cur.fetchall()

        all_teams = []
        for team in teams_raw:
            team_dict = dict(team)
            cur.execute("""
                SELECT g.* FROM golfers g
                JOIN team_golfers tg ON tg.golfer_id = g.id
                WHERE tg.team_id = %s
            """, (team_dict["id"],))
            team_dict["golfers"] = [dict(g) for g in cur.fetchall()]
            all_teams.append(team_dict)

        scores = calc_all_team_scores(all_teams)

        for team_id, result in scores.items():
            logger.info(
                f"Team {team_id}: raw={result['raw']} "
                f"bonus={result['bonus']} final={result['final']}"
            )
            cur.execute("""
                UPDATE teams SET final_score=%s, bonus_shots=%s, dk_total_points=%s
                WHERE id=%s
            """, (result["final"], result["bonus"], result["final"], team_id))

        conn.commit()
        cur.close()
        conn.close()
        logger.info("=== Score refresh complete ===")

    except Exception as e:
        logger.error(f"Score refresh failed: {e}", exc_info=True)