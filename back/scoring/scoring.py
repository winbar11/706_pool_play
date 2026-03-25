"""
DraftKings Golf Scoring Engine
Per-hole scoring + bonuses applied end-of-round.
"""

# Per-hole points
HOLE_POINTS = {
    "double_eagle": 20.0,
    "eagle":        8.0,
    "birdie":       3.0,
    "par":          0.5,
    "bogey":       -0.5,
    "double_bogey":-1.0,
    "worse":       -1.0,
    "ace":         10.0,   # bonus on top of eagle/birdie scoring
}

# Finishing position bonus
FINISH_BONUS = {
    1: 30, 2: 20, 3: 18, 4: 16, 5: 14, 6: 12, 7: 10,
    8: 9, 9: 8, 10: 7,
    **{p: 6 for p in range(11, 16)},
    **{p: 5 for p in range(16, 21)},
    **{p: 4 for p in range(21, 26)},
    **{p: 3 for p in range(26, 31)},
    **{p: 2 for p in range(31, 41)},
    **{p: 1 for p in range(41, 51)},
}

STREAK_BONUS     = 3.0  # 3+ consecutive birdies or better (max 1/round)
BOGEY_FREE_BONUS = 3.0  # no bogeys/worse in a round
ALL4_UNDER70     = 5.0  # all 4 rounds under 70 strokes

def calc_round_points(birdies, eagles, bogeys, doubles, worse, pars,
                        ace, double_eagle, bogey_free, birdie_streak) -> float:
    pts  = double_eagle * HOLE_POINTS["double_eagle"]
    pts += eagles       * HOLE_POINTS["eagle"]
    pts += birdies      * HOLE_POINTS["birdie"]
    pts += pars         * HOLE_POINTS["par"]
    pts += bogeys       * HOLE_POINTS["bogey"]
    pts += doubles      * HOLE_POINTS["double_bogey"]
    pts += worse        * HOLE_POINTS["worse"]
    if ace:
        pts += HOLE_POINTS["ace"]
    if bogey_free:
        pts += BOGEY_FREE_BONUS
    if birdie_streak:
        pts += STREAK_BONUS
    return round(pts, 2)

def calc_total_points(golfer: dict) -> float:
    """
    Re-compute all DK points from stored round stats.
    Call after updating golfer hole data from ESPN.
    """
    total = 0.0
    for r in range(1, 5):
        total += calc_round_points(
            golfer.get(f"r{r}_birdies", 0) or 0,
            golfer.get(f"r{r}_eagles", 0) or 0,
            golfer.get(f"r{r}_bogeys", 0) or 0,
            golfer.get(f"r{r}_doubles", 0) or 0,
            golfer.get(f"r{r}_worse", 0) or 0,
            golfer.get(f"r{r}_pars", 0) or 0,
            golfer.get(f"r{r}_ace", 0) or 0,
            golfer.get(f"r{r}_double_eagle", 0) or 0,
            golfer.get(f"r{r}_bogey_free", 0) or 0,
            golfer.get(f"r{r}_birdie_streak", 0) or 0,
        )

    # All-4-rounds-under-70 bonus
    scores = [golfer.get(f"round{r}_score") for r in range(1, 5)]
    if all(s is not None and s < 70 for s in scores):
        total += ALL4_UNDER70

    # Finish position bonus (added once at end of tournament)
    pos = golfer.get("finish_position")
    if pos and golfer.get("current_round", 0) == 4:
        total += FINISH_BONUS.get(int(pos), 0)

    return round(total, 2)

def calc_team_points(golfers: list[dict]) -> float:
    return round(sum(g.get("dk_total_points", 0) or 0 for g in golfers), 2)