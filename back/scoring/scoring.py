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
    made_cut      = golfer.get("made_cut", 1)
    total_score   = golfer.get("total_score")
    current_round = golfer.get("current_round", 0)

    if current_round == 0 or total_score is None:
        return 0

    if made_cut == 0:
        return int(total_score) + MISSED_CUT_PENALTY

    return int(total_score)


def calc_team_raw_score(golfers: list) -> int:
    return sum(calc_golfer_score(g) for g in golfers)


def calc_best_round_bonuses(all_teams: list, all_golfers: list = None) -> dict:
    bonuses = {team["id"]: 0 for team in all_teams}

    # Use all golfers in the field for uniqueness check (not just drafted ones)
    field = all_golfers if all_golfers is not None else [
        g for team in all_teams for g in team.get("golfers", [])
    ]

    for round_num in range(1, 5):
        score_key = f"round{round_num}_score"

        golfer_scores = {}
        for g in field:
            gid   = g["id"]
            score = g.get(score_key)
            if score is not None and score >= 60 and gid not in golfer_scores:
                golfer_scores[gid] = score

        if not golfer_scores:
            continue

        best_score   = min(golfer_scores.values())
        best_golfers = [gid for gid, s in golfer_scores.items() if s == best_score]

        if len(best_golfers) != 1:
            continue

        winning_golfer_id = best_golfers[0]
        for team in all_teams:
            for g in team.get("golfers", []):
                if g["id"] == winning_golfer_id:
                    bonuses[team["id"]] -= 1
                    break

    return bonuses


def calc_solo_leader_bonuses(all_teams: list) -> dict:
    bonuses = {team["id"]: 0 for team in all_teams}

    for round_num in range(1, 5):
        leader_key = f"solo_leader_r{round_num}"
        for team in all_teams:
            for g in team.get("golfers", []):
                if g.get(leader_key) == 1:
                    bonuses[team["id"]] -= 1

    return bonuses


def calc_winner_bonuses(all_teams: list, tournament_complete: bool = False) -> dict:
    bonuses = {team["id"]: 0 for team in all_teams}

    if not tournament_complete:
        return bonuses

    for team in all_teams:
        for g in team.get("golfers", []):
            if (g.get("finish_position") == 1 and
                    g.get("current_round", 0) == 4 and
                    g.get("made_cut", 1) == 1):
                bonuses[team["id"]] -= 5
                break

    return bonuses


def calc_all_team_scores(all_teams: list, tournament_complete: bool = False, all_golfers: list = None) -> dict:
    best_round  = calc_best_round_bonuses(all_teams, all_golfers)
    solo_leader = calc_solo_leader_bonuses(all_teams)
    winner      = calc_winner_bonuses(all_teams, tournament_complete)

    results = {}
    for team in all_teams:
        tid   = team["id"]
        raw   = calc_team_raw_score(team.get("golfers", []))
        bonus = best_round.get(tid, 0) + solo_leader.get(tid, 0) + winner.get(tid, 0)
        final = raw + bonus
        results[tid] = {"raw": raw, "bonus": bonus, "final": final}

    return results