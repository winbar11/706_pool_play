from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import delete, update
from database.db import get_session, to_dict, _seed_golfers, sync_golfer_rankings
from database.models import Golfer, Team, TournamentSetting, User, team_golfers
from dependencies import get_admin_user
from scoring.scoring import calc_golfer_score, calc_all_team_scores
from scheduler.scheduler import refresh_scores
import asyncio

router = APIRouter()

@router.post("/lock-teams")
def lock_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.get(TournamentSetting, "teams_locked").value = "1"
    return {"message": "Teams locked. No more changes allowed."}

@router.post("/unlock-teams")
def unlock_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.get(TournamentSetting, "teams_locked").value = "0"
    return {"message": "Teams unlocked."}

@router.post("/refresh-scores")
async def trigger_refresh(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    asyncio.create_task(refresh_scores())
    return {"message": "Score refresh triggered (running in background)"}

class ManualGolferUpdate(BaseModel):
    golfer_id:    int
    round_num:    int
    round_score:  int = None
    total_score:  int = None
    made_cut:     int = 1
    finish_position: int = None

@router.post("/update-golfer")
def manual_update_golfer(req: ManualGolferUpdate, authorization: str = Header(None)):
    """
    Manual score entry. Updates round score and total score,
    then recalculates all team final scores.
    """
    get_admin_user(authorization=authorization)

    with get_session() as session:
        golfer = session.get(Golfer, req.golfer_id)
        if not golfer:
            raise HTTPException(404, "Golfer not found")

        r = req.round_num

        # Build update fields
        updates = {}
        if req.round_score is not None:
            updates[f"round{r}_score"] = req.round_score
        if req.total_score is not None:
            updates["total_score"]   = req.total_score
            updates["current_round"] = r
        if req.finish_position is not None:
            updates["finish_position"] = req.finish_position
        updates["made_cut"] = req.made_cut

        for k, v in updates.items():
            setattr(golfer, k, v)

        # Recalculate all team scores
        teams = session.query(Team).all()
        all_teams = [
            {**to_dict(team), "golfers": [to_dict(g) for g in team.golfers]}
            for team in teams
        ]

        tc_row = session.get(TournamentSetting, "tournament_complete")
        tournament_complete = tc_row is not None and tc_row.value == "1"

        scores = calc_all_team_scores(all_teams, tournament_complete)
        for team_id, result in scores.items():
            team = session.get(Team, team_id)
            team.final_score = result["final"]
            team.bonus_shots = result["bonus"]
            team.dk_total_points = result["final"]

    return {"message": f"Golfer updated and team scores recalculated"}

@router.get("/users")
def list_users(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        users = session.query(User).order_by(User.created_at).all()
        fields = ["id", "username", "email", "phone", "is_admin", "paid", "created_at"]
        return {"users": [{f: getattr(u, f) for f in fields} for u in users]}

@router.post("/set-paid")
def set_paid(user_id: int, paid: bool, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            user.paid = 1 if paid else 0
    return {"message": "Paid status updated"}

@router.post("/set-round")
def set_round(round_num: int, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.get(TournamentSetting, "current_round").value = str(round_num)
    return {"message": f"Current round set to {round_num}"}

@router.post("/set-tournament-complete")
def set_tournament_complete(complete: bool, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.get(TournamentSetting, "tournament_complete").value = "1" if complete else "0"
    return {"message": "Tournament marked complete." if complete else "Tournament marked in-progress."}

class DeleteTeamsRequest(BaseModel):
    team_ids: List[int]

@router.post("/delete-teams")
def delete_teams(req: DeleteTeamsRequest, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    if not req.team_ids:
        raise HTTPException(400, "No team IDs provided")
    with get_session() as session:
        session.execute(delete(team_golfers).where(team_golfers.c.team_id.in_(req.team_ids)))
        result = session.execute(delete(Team).where(Team.id.in_(req.team_ids)))
        deleted = result.rowcount
    return {"message": f"{deleted} team(s) deleted successfully", "deleted_count": deleted}

@router.post("/clear-teams")
def clear_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.execute(delete(team_golfers))
        session.execute(delete(Team))
    return {"message": "All teams cleared successfully"}

@router.post("/sync-rankings")
def sync_rankings(authorization: str = Header(None)):
    """Update world_rank, salary, and country from seed data without touching teams."""
    get_admin_user(authorization=authorization)
    updated = sync_golfer_rankings()
    return {"message": f"Rankings synced. {updated} golfer(s) updated.", "updated": updated}

@router.post("/reset-golfers")
def reset_golfers(authorization: str = Header(None)):
    """Wipe the golfer field and all teams, then re-seed from db.py."""
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.execute(delete(team_golfers))
        session.execute(delete(Team))
        session.execute(delete(Golfer))
    _seed_golfers()
    return {"message": "Golfer field reset and re-seeded. All teams cleared."}

@router.post("/set-theme")
def set_theme(theme: str, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    if theme not in ("masters", "us-open", "open-championship"):
        raise HTTPException(400, "Invalid theme. Must be 'masters', 'us-open', or 'open-championship'")
    with get_session() as session:
        session.get(TournamentSetting, "theme").value = theme
    return {"message": f"Theme set to {theme}", "theme": theme}

@router.post("/set-pot")
def set_pot(amount: int, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.get(TournamentSetting, "pot_amount").value = str(amount)
    return {"message": f"Pot amount set to ${amount}"}

@router.post("/clear-scores")
def clear_scores(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    with get_session() as session:
        session.execute(update(Golfer).values(
            current_round=0,
            total_score=None,
            made_cut=1,
            finish_position=None,
            round1_score=None,
            round2_score=None,
            round3_score=None,
            round4_score=None,
            solo_leader_r1=0,
            solo_leader_r2=0,
            solo_leader_r3=0,
            solo_leader_r4=0,
        ))
        session.execute(update(Team).values(final_score=0, bonus_shots=0, dk_total_points=0))
    return {"message": "All scores cleared successfully"}
