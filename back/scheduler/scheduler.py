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

        # DEBUG — log first 5 players to see what ESPN is returning
        logger.info("Sample players from ESPN:")
        for p in players[:5]:
            logger.info(
                f"  {p['name']}: round={p['current_round']}, "
                f"r1={p.get('round1_score')}, r2={p.get('round2_score')}, "
                f"r3={p.get('round3_score')}, r4={p.get('round4_score')}, "
                f"total={p.get('total_score')}, made_cut={p.get('made_cut')}"
            )

        conn = get_conn()
        cur = conn.cursor()
        matched = 0

        for player in players:
            espn_id = player["espn_id"]
            name    = player["name"]

            cur.execute("SELECT * FROM golfers WHERE espn_id LIKE %s", (f"{espn_id}%",))
            row = cur.fetchone()

            if not row:
                cur.execute("SELECT * FROM golfers WHERE name LIKE %s", (f"%{name}%",))
                row = cur.fetchone()

            if not row:
                logger.debug(f"No DB match for: {name} (ESPN id: {espn_id})")
                continue

            matched += 1
            golfer        = dict(row)
            current_round = player.get("current_round", 0)

            logger.info(
                f"  Updating {name}: current_round={current_round}, "
                f"r1={player.get('round1_score')}, r2={player.get('round2_score')}, "
                f"r3={player.get('round3_score')}, r4={player.get('round4_score')}"
            )

            updates = {
                "current_round":   current_round,
                "total_score":     player.get("total_score"),
                "made_cut":        player.get("made_cut", 1),
                "finish_position": player.get("finish_position"),
            }

            for r in range(1, 5):
                rs = player.get(f"round{r}_score")
                if rs is not None:
                    updates[f"round{r}_score"] = rs

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

                logger.info(
                    f"    Round {r}: score={stats.get('round_score')}, "
                    f"birdies={stats['birdies']}, bogeys={stats['bogeys']}, "
                    f"dk_pts={round_pts}"
                )

            merged = {**golfer, **updates}
            updates["dk_total_points"] = calc_total_points(merged)

            logger.info(f"    Total DK pts: {updates['dk_total_points']}")

            set_clause = ", ".join(f"{k}=%s" for k in updates)
            cur.execute(
                f"UPDATE golfers SET {set_clause} WHERE id=%s",
                (*updates.values(), golfer["id"])
            )

        logger.info(f"Matched and updated {matched}/{len(players)} players")

        cur.execute("SELECT * FROM teams")
        teams = cur.fetchall()
        for team in teams:
            cur.execute("""
                SELECT g.* FROM golfers g
                JOIN team_golfers tg ON tg.golfer_id = g.id
                WHERE tg.team_id = %s
            """, (team["id"],))
            golfer_rows = cur.fetchall()
            total = calc_team_points([dict(g) for g in golfer_rows])
            cur.execute("UPDATE teams SET dk_total_points=%s WHERE id=%s",
                        (total, team["id"]))

        conn.commit()
        cur.close()
        conn.close()
        logger.info("=== Score refresh complete ===")

    except Exception as e:
        logger.error(f"Score refresh failed: {e}", exc_info=True)