"""
ESPN unofficial golf API integration.
No API key required.
"""
import httpx
import logging
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)

# The Masters 2026
TOURNEY_ID    = "401811941"

LEADERBOARD_URL = f"https://site.api.espn.com/apis/site/v2/sports/golf/leaderboard?event={TOURNEY_ID}"

async def fetch_leaderboard() -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(LEADERBOARD_URL)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"ESPN leaderboard fetch failed: {e}")
        return None

def parse_leaderboard(data: dict) -> list[dict]:
    players = []
    try:
        events = data.get("events", [])
        if not events:
            logger.warning("No events in ESPN response")
            return []

        competitions = events[0].get("competitions", [])
        if not competitions:
            logger.warning("No competitions in ESPN event")
            return []

        competitors   = competitions[0].get("competitors", [])
        current_round = competitions[0].get("status", {}).get("period", 0)

        for c in competitors:
            athlete    = c.get("athlete", {})
            status     = c.get("status", {})
            stat_type  = status.get("type", {})
            pos        = status.get("position", {})
            status_name = stat_type.get("name", "")

            # Log any unexpected status types for debugging
            if status_name not in (
                "STATUS_IN_PROGRESS", "STATUS_FINISH",
                "STATUS_SCHEDULED", "STATUS_CUT",
                "STATUS_WD", "STATUS_DQ"
            ):
                logger.debug(f"Unknown status for {athlete.get('displayName')}: {status_name}")

            made_cut = 0 if status_name in ("STATUS_CUT", "STATUS_WD", "STATUS_DQ") else 1

            # Finish position — strip T prefix, return None if 0 or invalid
            pos_display = pos.get("displayName", "")
            finish_pos  = _parse_position(pos_display)

            # Score to par from statistics array — this is the correct field
            score_to_par = 0
            for s in c.get("statistics", []):
                if s.get("name") == "scoreToPar":
                    raw = s.get("value", 0)
                    # Scheduled players have displayValue of "-" meaning E/0
                    display = s.get("displayValue", "")
                    if display in ("-", "--", ""):
                        score_to_par = 0
                    else:
                        try:
                            score_to_par = int(raw) if raw is not None else 0
                        except (ValueError, TypeError):
                            score_to_par = 0
                    break

            # Round scores from linescores — only store completed rounds (>= 60 strokes).
            # Skip the current period for in-progress players: their linescore is a
            # running stroke count (e.g. 63 through 9 holes) that looks like a low
            # score but isn't a finished round.
            linescores   = c.get("linescores", [])
            round_scores = {}
            for ls in linescores:
                period = ls.get("period")
                val    = ls.get("value")
                if period and val is not None:
                    score_val = float(val)
                    if score_val >= 60 and not (
                        status_name == "STATUS_IN_PROGRESS" and period == current_round
                    ):
                        round_scores[period] = int(score_val)

            players.append({
                "espn_id":         str(athlete.get("id", "")),
                "name":            athlete.get("displayName", ""),
                "finish_position": finish_pos,
                "total_score":     score_to_par,
                "current_round":   current_round,
                "made_cut":        made_cut,
                "in_progress":     status_name == "STATUS_IN_PROGRESS",
                "round1_score":    round_scores.get(1),
                "round2_score":    round_scores.get(2),
                "round3_score":    round_scores.get(3),
                "round4_score":    round_scores.get(4),
            })

    except Exception as e:
        logger.error(f"Parse leaderboard error: {e}", exc_info=True)

    logger.info(f"Parsed {len(players)} players from ESPN leaderboard")
    return players

def _parse_position(pos: str) -> Optional[int]:
    if not pos or pos in ("-", "--", "0"):
        return None
    pos = pos.lstrip("T")
    try:
        result = int(pos)
        return result if result > 0 else None
    except ValueError:
        return None