"""
706 Masters Pool Scoring Engine
================================
Core: Sum of all 6 golfers' scores to par. LOWEST total wins.

Bonuses (subtract from team total):
  - Best round of day (unique across ALL golfers in tournament): -1 shot
  - Solo leader after any round: -1 shot per round
  - Tournament winner picked: -5 shots

Penalties (add to team total):
  - Missed cut / WD / DQ: actual 2-round score + 8 penalty shots
  - Late WD (never played): +8 penalty
"""

MISSED_CUT_PENALTY = 8

def calc_golfer_score(golfer: dict) -> int:
    """
    Returns a golfer's contribution to their team's score.
    - Active/finished: their actual total score to par
    - Missed cut / WD: their 36-hole score + 8 penalty
    - Never played: +8 flat
    """
    made_cut    = golfer.get("made_cut", 1)
    total_score = golfer.get("total_score")
    current_round = golfer.get("current_round", 0)

    # Never teed off
    if current_round == 0 and total_score is None:
        return MISSED_CUT_PENALTY

    # Missed cut or WD
    if made_cut == 0:
        base = total_score if total_score is not None else 0
        return base + MISSED_CUT_PENALTY

    # Active or finished — use actual score to par
    return total_score if total_score is not None else 0


def calc_team_raw_score(golfers: list) -> int:
    """Sum of all 6 golfers' scores. Before bonuses."""
    return sum(calc_golfer_score(g) for g in golfers)


def calc_best_round_bonuses(all_teams: list) -> dict:
    """
    For each round (1-4), find the single lowest round score
    across ALL golfers in the tournament. If that score is unique
    (only one golfer shot it), every team that owns that golfer
    gets -1 bonus for that round.

    Returns: dict of {team_id: bonus_shots (negative number)}
    """
    bonuses = {team["id"]: 0 for team in all_teams}

    for round_num in range(1, 5):
        score_key = f"round{round_num}_score"

        # Collect all round scores across all golfers across all teams
        # Build a map: golfer_id -> round_score
        golfer_scores = {}
        for team in all_teams:
            for g in team.get("golfers", []):
                gid   = g["id"]
                score = g.get(score_key)
                if score is not None and gid not in golfer_scores:
                    golfer_scores[gid] = score

        if not golfer_scores:
            continue

        # Find the lowest score this round
        best_score = min(golfer_scores.values())

        # Find all golfers who shot that score
        best_golfers = [gid for gid, s in golfer_scores.items() if s == best_score]

        # Only award bonus if exactly ONE golfer shot the best round
        if len(best_golfers) != 1:
            continue

        winning_golfer_id = best_golfers[0]

        # Give -1 to every team that owns this golfer
        for team in all_teams:
            for g in team.get("golfers", []):
                if g["id"] == winning_golfer_id:
                    bonuses[team["id"]] -= 1
                    break

    return bonuses


def calc_solo_leader_bonuses(all_teams: list) -> dict:
    """
    For each round (1-4), check if a golfer was the SOLE leader
    after that round. If so, every team owning that golfer gets -1.

    We track this via the solo_leader_rX fields on each golfer.
    Returns: dict of {team_id: bonus_shots (negative number)}
    """
    bonuses = {team["id"]: 0 for team in all_teams}

    for round_num in range(1, 5):
        leader_key = f"solo_leader_r{round_num}"
        for team in all_teams:
            for g in team.get("golfers", []):
                if g.get(leader_key) == 1:
                    bonuses[team["id"]] -= 1

    return bonuses


def calc_winner_bonuses(all_teams: list) -> dict:
    """
    If a team's golfer won the tournament (finish_position=1,
    current_round=4, made_cut=1), that team gets -5.
    Returns: dict of {team_id: bonus_shots (negative number)}
    """
    bonuses = {team["id"]: 0 for team in all_teams}

    for team in all_teams:
        for g in team.get("golfers", []):
            if (g.get("finish_position") == 1 and
                    g.get("current_round", 0) == 4 and
                    g.get("made_cut", 1) == 1):
                bonuses[team["id"]] -= 5
                break  # max one winner per team

    return bonuses


def calc_all_team_scores(all_teams: list) -> dict:
    """
    Master function. Returns final score for each team including
    all bonuses.

    Returns: dict of {team_id: {"raw": int, "bonus": int, "final": int}}
    """
    best_round  = calc_best_round_bonuses(all_teams)
    solo_leader = calc_solo_leader_bonuses(all_teams)
    winner      = calc_winner_bonuses(all_teams)

    results = {}
    for team in all_teams:
        tid     = team["id"]
        raw     = calc_team_raw_score(team.get("golfers", []))
        bonus   = best_round.get(tid, 0) + solo_leader.get(tid, 0) + winner.get(tid, 0)
        final   = raw + bonus
        results[tid] = {"raw": raw, "bonus": bonus, "final": final}

    return results