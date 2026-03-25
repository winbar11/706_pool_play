"""
End-of-round score refresh job.
Fetches ESPN data, updates golfer stats, recalculates DK points,
updates all team totals.
"""
import asyncio
import logging
from database.db import get_conn
from clients.espn_client import fetch_leaderboard, fetch_scorecard, parse_leaderboard, parse_scorecard
from scoring.scoring import calc_round_points, calc_total_points, calc_team_points

logger = logging.getLogger(__name__)

async def refresh_scores():
    logger.info("=== Starting end-of-round score refresh ===")
    try:
        lb_data = await fetch_leaderboard()
        if not lb_data:
            logger.warning("No leaderboard data returned from ESPN")
            return

        players = parse_leaderboard(lb_data)
        conn = get_conn()

        for player in players:
            espn_id = player["espn_id"]
            # Find golfer by name (ESPN IDs may differ from seeded data)
            row = conn.execute(
                "SELECT * FROM golfers WHERE name LIKE ? OR espn_id LIKE ?",
                (f"%{player['name']}%", f"{espn_id}%")
            ).fetchone()

            if not row:
                logger.debug(f"Golfer not found in DB: {player['name']}")
                continue

            golfer = dict(row)
            current_round = player.get("current_round", 0)
            updates = {
                "current_round":  current_round,
                "total_score":    player.get("total_score"),
                "made_cut":       player.get("made_cut", 1),
                "finish_position": player.get("finish_position"),
            }

            # Fetch scorecards for completed rounds
            for r in range(1, current_round + 1):
                sc = await fetch_scorecard(espn_id, r) if espn_id else None
                if sc:
                    stats = parse_scorecard(sc, r)
                    updates[f"round{r}_score"]     = stats["round_score"]
                    updates[f"r{r}_birdies"]        = stats["birdies"]
                    updates[f"r{r}_eagles"]         = stats["eagles"]
                    updates[f"r{r}_bogeys"]         = stats["bogeys"]
                    updates[f"r{r}_doubles"]        = stats["doubles"]
                    updates[f"r{r}_worse"]          = stats["worse"]
                    updates[f"r{r}_pars"]           = stats["pars"]
                    updates[f"r{r}_ace"]            = stats["ace"]
                    updates[f"r{r}_double_eagle"]   = stats["double_eagle"]
                    updates[f"r{r}_bogey_free"]     = stats["bogey_free"]
                    updates[f"r{r}_birdie_streak"]  = stats["birdie_streak"]

                    round_pts = calc_round_points(
                        stats["birdies"], stats["eagles"], stats["bogeys"],
                        stats["doubles"], stats["worse"], stats["pars"],
                        stats["ace"], stats["double_eagle"],
                        stats["bogey_free"], stats["birdie_streak"]
                    )
                    updates[f"dk_r{r}_points"] = round_pts

            # Recalculate totals
            merged = {**golfer, **updates}
            updates["dk_total_points"] = calc_total_points(merged)

            set_clause = ", ".join(f"{k}=?" for k in updates)
            conn.execute(
                f"UPDATE golfers SET {set_clause} WHERE id=?",
                (*updates.values(), golfer["id"])
            )

        # Recalculate all team totals
        teams = conn.execute("SELECT * FROM teams").fetchall()
        for team in teams:
            golfer_rows = conn.execute("""
                SELECT g.* FROM golfers g
                JOIN team_golfers tg ON tg.golfer_id = g.id
                WHERE tg.team_id = ?
            """, (team["id"],)).fetchall()
            total = calc_team_points([dict(g) for g in golfer_rows])
            conn.execute("UPDATE teams SET dk_total_points=? WHERE id=?",
                        (total, team["id"]))

        conn.commit()
        conn.close()
        logger.info("=== Score refresh complete ===")

    except Exception as e:
        logger.error(f"Score refresh failed: {e}", exc_info=True)

async def fetch_scorecard(espn_id: str, round_num: int):
    from clients.espn_client import fetch_scorecard as _fetch, MASTERS_TOURNAMENT_ID
    return await _fetch(espn_id)