"""
End-of-round score refresh job.
Fetches ESPN data, updates golfer stats, recalculates DK points,
updates all team totals.
"""
import asyncio
import logging
from database.db import get_conn
from clients.espn_client import fetch_leaderboard, parse_leaderboard, calc_hole_stats_from_rounds
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
        if not players:
            logger.warning("No players parsed from leaderboard")
            return

        logger.info(f"Processing {len(players)} players from ESPN")
        conn = get_conn()
        matched = 0

        for player in players:
            espn_id = player["espn_id"]
            name    = player["name"]

            # Match by ESPN ID first, then fall back to name
            row = conn.execute(
                "SELECT * FROM golfers WHERE espn_id LIKE ?", (f"{espn_id}%",)
            ).fetchone()

            if not row:
                # Try name match — strip accents won't matter for most names
                row = conn.execute(
                    "SELECT * FROM golfers WHERE name LIKE ?", (f"%{name}%",)
                ).fetchone()

            if not row:
                logger.debug(f"No DB match for: {name} (ESPN id: {espn_id})")
                continue

            matched += 1
            golfer        = dict(row)
            current_round = player.get("current_round", 0)

            updates = {
                "current_round":  current_round,
                "total_score":    player.get("total_score"),
                "made_cut":       player.get("made_cut", 1),
                "finish_position": player.get("finish_position"),
            }

            # Store round scores
            for r in range(1, 5):
                rs = player.get(f"round{r}_score")
                if rs is not None:
                    updates[f"round{r}_score"] = rs

            # Estimate hole stats from round scores for DK calc
            round_scores = {
                r: player.get(f"round{r}_score")
                for r in range(1, current_round + 1)
                if player.get(f"round{r}_score") is not None
            }
            hole_stats = calc_hole_stats_from_rounds(round_scores)

            for r, stats in hole_stats.items():
                updates[f"r{r}_birdies"]       = stats["birdies"]
                updates[f"r{r}_eagles"]        = stats["eagles"]
                updates[f"r{r}_bogeys"]        = stats["bogeys"]
                updates[f"r{r}_doubles"]       = stats["doubles"]
                updates[f"r{r}_worse"]         = stats["worse"]
                updates[f"r{r}_pars"]          = stats["pars"]
                updates[f"r{r}_ace"]           = stats["ace"]
                updates[f"r{r}_double_eagle"]  = stats["double_eagle"]
                updates[f"r{r}_bogey_free"]    = stats["bogey_free"]
                updates[f"r{r}_birdie_streak"] = stats["birdie_streak"]

                round_pts = calc_round_points(
                    stats["birdies"], stats["eagles"], stats["bogeys"],
                    stats["doubles"], stats["worse"], stats["pars"],
                    stats["ace"], stats["double_eagle"],
                    stats["bogey_free"], stats["birdie_streak"]
                )
                updates[f"dk_r{r}_points"] = round_pts

            # Recalculate total DK points
            merged = {**golfer, **updates}
            updates["dk_total_points"] = calc_total_points(merged)

            set_clause = ", ".join(f"{k}=?" for k in updates)
            conn.execute(
                f"UPDATE golfers SET {set_clause} WHERE id=?",
                (*updates.values(), golfer["id"])
            )

        logger.info(f"Matched and updated {matched}/{len(players)} players")

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