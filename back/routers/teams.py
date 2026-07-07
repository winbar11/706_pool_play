from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database.db import get_session, to_dict
from database.models import Golfer, Team, TournamentSetting
from dependencies import get_current_user

router = APIRouter()

SALARY_CAP = 50000
ROSTER_SIZE = 6
MAX_TEAMS = 1

class TeamSubmit(BaseModel):
    team_name: str
    golfer_ids: list[int]
    team_id: int | None = None

def _team_dict(team: Team) -> dict:
    golfers = sorted(team.golfers, key=lambda g: (g.total_score is None, g.total_score))
    return {**to_dict(team), "golfers": [to_dict(g) for g in golfers]}

@router.post("/submit")
def submit_team(req: TeamSubmit, authorization: str = Header(None)):
    user = get_current_user(authorization)

    with get_session() as session:
        locked = session.get(TournamentSetting, "teams_locked")
        if locked and locked.value == "1":
            raise HTTPException(400, "Tournament has started — teams are locked")

        if len(req.golfer_ids) != ROSTER_SIZE:
            raise HTTPException(400, f"Must select exactly {ROSTER_SIZE} golfers")

        if len(set(req.golfer_ids)) != ROSTER_SIZE:
            raise HTTPException(400, "Duplicate golfers not allowed")

        golfers = []
        for gid in req.golfer_ids:
            g = session.get(Golfer, gid)
            if not g:
                raise HTTPException(404, f"Golfer id {gid} not found")
            golfers.append(g)

        total_salary = sum(g.salary for g in golfers)
        if total_salary > SALARY_CAP:
            raise HTTPException(400,
                f"Salary cap exceeded: ${total_salary:,} > ${SALARY_CAP:,}")

        if req.team_id is not None:
            # Update existing team — verify ownership
            team = session.get(Team, req.team_id)
            if not team or team.user_id != user["id"]:
                raise HTTPException(404, "Team not found")
            team.team_name = req.team_name
            team.total_salary = total_salary
            team.golfers = golfers
        else:
            # Create new team — enforce per-user cap
            count = session.query(Team).filter(Team.user_id == user["id"]).count()
            if count >= MAX_TEAMS:
                raise HTTPException(400, f"You may have at most {MAX_TEAMS} teams")
            team = Team(
                user_id=user["id"], team_name=req.team_name, total_salary=total_salary,
                final_score=0, bonus_shots=0, dk_total_points=0, golfers=golfers,
            )
            session.add(team)

        session.flush()
        team_id = team.id

    return {"message": "Team submitted successfully", "team_id": team_id,
            "total_salary": total_salary}

@router.get("/my")
def my_teams(authorization: str = Header(None)):
    user = get_current_user(authorization)
    with get_session() as session:
        teams = (
            session.query(Team)
            .filter(Team.user_id == user["id"])
            .order_by(Team.id.asc())
            .all()
        )
        return {"teams": [_team_dict(t) for t in teams]}

@router.get("/{team_id}")
def get_team(team_id: int):
    with get_session() as session:
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(404, "Team not found")
        return _team_dict(team)
