"""
ESPN unofficial golf API integration.
Fetches Masters leaderboard + hole-by-hole data.
No API key required.
"""
import httpx
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ESPN Masters tournament ID (yr. 2026) --> https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard
# TOURNEY_ID = "401811941"

# VALERO TEXAS OPEN TOURNAMENT
TOURNEY_ID = "401811940"

LEADERBOARD_URL = f"https://site.api.espn.com/apis/site/v2/sports/golf/leaderboard?event={TOURNEY_ID}"
SCORECARD_URL   = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scorecards/{athlete_id}?event={event_id}"

async def fetch_leaderboard() -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(LEADERBOARD_URL)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"ESPN leaderboard fetch failed: {e}")
        return None

async def fetch_scorecard(athlete_id: str) -> Optional[dict]:
    url = SCORECARD_URL.format(athlete_id=athlete_id, event_id=TOURNEY_ID)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"ESPN scorecard fetch failed for {athlete_id}: {e}")
        return None

def parse_leaderboard(data: dict) -> list[dict]:
    """Extract per-player summary from ESPN leaderboard JSON."""
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
            athlete   = c.get("athlete", {})
            status    = c.get("status", {})
            stat_type = status.get("type", {})
            pos       = status.get("position", {})

            # STATUS_CUT / STATUS_WD / STATUS_DQ = missed cut
            status_name = stat_type.get("name", "")
            made_cut = 0 if status_name in ("STATUS_CUT", "STATUS_WD", "STATUS_DQ") else 1

            # Strip T from "T4", "T26" to get numeric position
            pos_display = pos.get("displayName", "")
            finish_pos  = _parse_position(pos_display)

            # Pull round scores from linescores using period field
            linescores   = c.get("linescores", [])
            round_scores = {}
            for ls in linescores:
                period = ls.get("period")
                val    = ls.get("value")
                if period and val is not None:
                    round_scores[period] = int(val)

            players.append({
                "espn_id":         str(athlete.get("id", "")),
                "name":            athlete.get("displayName", ""),
                "finish_position": finish_pos,
                "total_score":     _parse_score(c.get("score", {}).get("displayValue", "E")),
                "current_round":   current_round,
                "made_cut":        made_cut,
                "round1_score":    round_scores.get(1),
                "round2_score":    round_scores.get(2),
                "round3_score":    round_scores.get(3),
                "round4_score":    round_scores.get(4),
            })

    except Exception as e:
        logger.error(f"Parse leaderboard error: {e}", exc_info=True)

    logger.info(f"Parsed {len(players)} players from ESPN leaderboard")
    return players

def parse_scorecard(data: dict, round_num: int) -> Optional[dict]:
    """
    Extract hole-level stats from a player's scorecard for a given round.
    Returns dict with birdies, eagles, bogeys, pars, doubles, worse, ace,
    double_eagle, bogey_free, birdie_streak.
    """
    result = dict(birdies=0, eagles=0, bogeys=0, doubles=0, worse=0, pars=0,
                    ace=0, double_eagle=0, bogey_free=0, birdie_streak=0,
                    round_score=None)
    try:
        rounds = data.get("rounds", [])
        if round_num > len(rounds):
            return result
        rd    = rounds[round_num - 1]
        holes = rd.get("linescores", [])
        total_strokes     = 0
        consecutive_under = 0
        max_consecutive   = 0
        has_bogey         = False

        for hole in holes:
            par       = int(hole.get("par", 4))
            value_raw = hole.get("value", "")
            try:
                strokes = int(value_raw)
            except (ValueError, TypeError):
                continue

            total_strokes += strokes
            diff = strokes - par

            if strokes == 1:
                result["ace"] += 1

            if diff <= -3:
                result["double_eagle"] += 1
                consecutive_under += 1
            elif diff == -2:
                result["eagles"] += 1
                consecutive_under += 1
            elif diff == -1:
                result["birdies"] += 1
                consecutive_under += 1
            elif diff == 0:
                result["pars"] += 1
                consecutive_under = 0
            elif diff == 1:
                result["bogeys"] += 1
                has_bogey = True
                consecutive_under = 0
            elif diff == 2:
                result["doubles"] += 1
                has_bogey = True
                consecutive_under = 0
            else:
                result["worse"] += 1
                has_bogey = True
                consecutive_under = 0

            max_consecutive = max(max_consecutive, consecutive_under)

        result["bogey_free"]    = 0 if has_bogey else 1
        result["birdie_streak"] = 1 if max_consecutive >= 3 else 0
        result["round_score"]   = total_strokes if total_strokes > 0 else None
    except Exception as e:
        logger.error(f"Parse scorecard error: {e}")
    return result

def _parse_score(s: str) -> Optional[int]:
    s = s.strip()
    if s in ("E", "-"):
        return 0
    try:
        return int(s)
    except ValueError:
        return None

def _parse_position(pos: str) -> Optional[int]:
    """Convert 'T4', '1', 'T26' etc to integer."""
    if not pos or pos in ("-", "--"):
        return None
    pos = pos.lstrip("T")
    try:
        return int(pos)
    except ValueError:
        return None

def _detect_round(competitor: dict) -> int:
    linescores = competitor.get("linescores", [])
    return len([l for l in linescores if l.get("value") not in (None, "", "--")])

def calc_hole_stats_from_rounds(round_scores: dict) -> dict:
    """
    ESPN leaderboard gives round totals as actual stroke counts (e.g. 68, 72).
    Par at TPC San Antonio is 72.
    Skip any round score that is 0 or unrealistically low (not yet played).
    """
    results = {}
    PAR = 72

    for r, score in round_scores.items():
        # Skip if score is None, 0, or unrealistic (no round under 55 in pro golf)
        if score is None or score < 55:
            continue

        diff = score - PAR
        if diff < 0:
            birdies = abs(diff)
            bogeys  = 0
        else:
            birdies = 0
            bogeys  = diff

        results[r] = {
            "birdies":       birdies,
            "eagles":        0,
            "bogeys":        bogeys,
            "doubles":       0,
            "worse":         0,
            "pars":          PAR - birdies - bogeys,
            "ace":           0,
            "double_eagle":  0,
            "bogey_free":    1 if bogeys == 0 else 0,
            "birdie_streak": 0,
            "round_score":   score,
        }

    return results