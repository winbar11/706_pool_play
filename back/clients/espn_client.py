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

# ESPN Masters tournament ID (The Masters = 2018)
MASTERS_TOURNAMENT_ID = "401580349"  # UPDATE EACH YEAR
LEADERBOARD_URL = f"https://site.api.espn.com/apis/site/v2/sports/golf/pga/leaderboard?event={MASTERS_TOURNAMENT_ID}"
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
    url = SCORECARD_URL.format(athlete_id=athlete_id, event_id=MASTERS_TOURNAMENT_ID)
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
            return []
        competitors = events[0].get("competitions", [{}])[0].get("competitors", [])
        for c in competitors:
            athlete = c.get("athlete", {})
            stats   = {s["name"]: s.get("displayValue", "0")
                        for s in c.get("statistics", [])}
            players.append({
                "espn_id":        str(athlete.get("id", "")),
                "name":           athlete.get("displayName", ""),
                "finish_position": c.get("status", {}).get("position", {}).get("id"),
                "total_score":    _parse_score(c.get("score", {}).get("displayValue", "E")),
                "current_round":  _detect_round(c),
                "made_cut":       1 if c.get("status", {}).get("type", {}).get("id") not in ("C", "W") else 0,
            })
    except Exception as e:
        logger.error(f"Parse leaderboard error: {e}")
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
        rd = rounds[round_num - 1]
        holes = rd.get("linescores", [])
        total_strokes = 0
        consecutive_under = 0
        max_consecutive = 0
        has_bogey = False

        for hole in holes:
            par        = int(hole.get("par", 4))
            value_raw  = hole.get("value", "")
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

def _detect_round(competitor: dict) -> int:
    linescores = competitor.get("linescores", [])
    return len([l for l in linescores if l.get("value") not in (None, "", "--")])