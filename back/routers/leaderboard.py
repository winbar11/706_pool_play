from fastapi import APIRouter
from sqlalchemy import nullslast
from database.db import get_session
from database.models import Team, TournamentSetting

router = APIRouter()

_GOLFER_FIELDS = [
    "id", "name", "salary", "world_rank",
    "current_round", "total_score", "made_cut", "finish_position",
    "round1_score", "round2_score", "round3_score", "round4_score",
    "solo_leader_r1", "solo_leader_r2", "solo_leader_r3", "solo_leader_r4",
]

def fmt_score(score):
    if score is None:
        return "—"
    if score == 0:
        return "E"
    return f"+{score}" if score > 0 else str(score)

@router.get("")
def leaderboard():
    with get_session() as session:
        teams = (
            session.query(Team)
            .order_by(nullslast(Team.final_score.asc()))
            .all()
        )

        result = []
        rank = 1
        for i, team in enumerate(teams):
            golfers = sorted(
                team.golfers,
                key=lambda g: (g.total_score is None, g.total_score),
            )

            # Assign tied rank: same score as previous team keeps the same rank
            if i > 0 and team.final_score == teams[i - 1].final_score:
                rank = result[-1]["rank"]
            else:
                rank = i + 1

            result.append({
                "id": team.id,
                "team_name": team.team_name,
                "total_salary": team.total_salary,
                "final_score": team.final_score,
                "bonus_shots": team.bonus_shots,
                "dk_total_points": team.dk_total_points,
                "is_locked": team.is_locked,
                "username": team.user.username,
                "rank": rank,
                "golfers": [{f: getattr(g, f) for f in _GOLFER_FIELDS} for g in golfers],
            })

        settings = session.query(TournamentSetting).all()
        s = {row.key: row.value for row in settings}

    return {"teams": result, "settings": s}
