from scoring.scoring import (
    calc_golfer_score,
    calc_team_raw_score,
    calc_best_round_bonuses,
    calc_solo_leader_bonuses,
    calc_winner_bonuses,
    calc_all_team_scores,
)


def golfer(**overrides):
    base = {"id": 1, "current_round": 1, "total_score": 0, "made_cut": 1}
    base.update(overrides)
    return base


# --- calc_golfer_score ---

def test_golfer_score_before_tournament_starts():
    assert calc_golfer_score(golfer(current_round=0, total_score=None)) == 0


def test_golfer_score_made_cut_uses_raw_total():
    assert calc_golfer_score(golfer(total_score=-5, made_cut=1)) == -5


def test_golfer_score_missed_cut_adds_penalty():
    assert calc_golfer_score(golfer(total_score=4, made_cut=0)) == 12


def test_team_raw_score_sums_all_golfers():
    golfers = [golfer(total_score=-2), golfer(id=2, total_score=3), golfer(id=3, total_score=0, made_cut=0)]
    assert calc_team_raw_score(golfers) == -2 + 3 + 8


# --- calc_best_round_bonuses ---

def test_best_round_bonus_awarded_to_unique_lowest():
    teams = [
        {"id": 1, "golfers": [{"id": 1, "round1_score": 66}]},
        {"id": 2, "golfers": [{"id": 2, "round1_score": 70}]},
    ]
    bonuses = calc_best_round_bonuses(teams)
    assert bonuses == {1: -1, 2: 0}


def test_best_round_bonus_withheld_on_tie():
    teams = [
        {"id": 1, "golfers": [{"id": 1, "round1_score": 66}]},
        {"id": 2, "golfers": [{"id": 2, "round1_score": 66}]},
    ]
    bonuses = calc_best_round_bonuses(teams)
    assert bonuses == {1: 0, 2: 0}


def test_best_round_bonus_ignores_scores_below_60():
    # Sub-60 scores are treated as not-yet-posted sentinel values, not real rounds
    teams = [
        {"id": 1, "golfers": [{"id": 1, "round1_score": 0}]},
        {"id": 2, "golfers": [{"id": 2, "round1_score": 68}]},
    ]
    bonuses = calc_best_round_bonuses(teams)
    assert bonuses == {1: 0, 2: -1}


def test_best_round_bonus_stacks_across_rounds():
    teams = [
        {"id": 1, "golfers": [{"id": 1, "round1_score": 66, "round2_score": 65}]},
        {"id": 2, "golfers": [{"id": 2, "round1_score": 70, "round2_score": 70}]},
    ]
    bonuses = calc_best_round_bonuses(teams)
    assert bonuses == {1: -2, 2: 0}


# --- calc_solo_leader_bonuses ---

def test_solo_leader_bonus_per_round():
    teams = [
        {"id": 1, "golfers": [{"id": 1, "solo_leader_r1": 1, "solo_leader_r2": 1}]},
        {"id": 2, "golfers": [{"id": 2, "solo_leader_r1": 0}]},
    ]
    bonuses = calc_solo_leader_bonuses(teams)
    assert bonuses == {1: -2, 2: 0}


# --- calc_winner_bonuses ---

def test_winner_bonus_only_when_tournament_complete():
    teams = [{"id": 1, "golfers": [{"id": 1, "finish_position": 1, "current_round": 4, "made_cut": 1}]}]
    assert calc_winner_bonuses(teams, tournament_complete=False) == {1: 0}
    assert calc_winner_bonuses(teams, tournament_complete=True) == {1: -5}


def test_winner_bonus_requires_completed_final_round():
    teams = [{"id": 1, "golfers": [{"id": 1, "finish_position": 1, "current_round": 3, "made_cut": 1}]}]
    assert calc_winner_bonuses(teams, tournament_complete=True) == {1: 0}


# --- calc_all_team_scores ---

def test_all_team_scores_combines_raw_and_bonuses():
    teams = [
        {
            "id": 1,
            "golfers": [
                {"id": 1, "total_score": -3, "made_cut": 1, "current_round": 4,
                 "round1_score": 65, "finish_position": 1},
            ],
        },
        {
            "id": 2,
            "golfers": [
                {"id": 2, "total_score": 2, "made_cut": 1, "current_round": 4, "round1_score": 71},
            ],
        },
    ]
    results = calc_all_team_scores(teams, tournament_complete=True)

    # Team 1: raw -3, best-round bonus -1, winner bonus -5 => final -9
    assert results[1] == {"raw": -3, "bonus": -6, "final": -9}
    # Team 2: raw 2, no bonuses
    assert results[2] == {"raw": 2, "bonus": 0, "final": 2}
