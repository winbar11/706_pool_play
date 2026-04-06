from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import List
from database.db import get_conn, _seed_golfers
from dependencies import get_admin_user
from scoring.scoring import calc_golfer_score, calc_all_team_scores
from scheduler.scheduler import refresh_scores
import asyncio

router = APIRouter()

@router.post("/lock-teams")
def lock_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tournament_settings SET value='1' WHERE key='teams_locked'")
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Teams locked. No more changes allowed."}

@router.post("/unlock-teams")
def unlock_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tournament_settings SET value='0' WHERE key='teams_locked'")
    conn.commit()
    cur.close()
    conn.close()
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
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM golfers WHERE id=%s", (req.golfer_id,))
    golfer = cur.fetchone()
    if not golfer:
        cur.close()
        conn.close()
        raise HTTPException(404, "Golfer not found")

    r = req.round_num

    # Build update fields
    updates = {}
    if req.round_score is not None:
        updates[f"round{r}_score"] = req.round_score
    if req.total_score is not None:
        updates["total_score"]     = req.total_score
        updates["current_round"]   = r
    if req.finish_position is not None:
        updates["finish_position"] = req.finish_position
    updates["made_cut"] = req.made_cut

    if updates:
        set_clause = ", ".join(f"{k}=%s" for k in updates)
        cur.execute(
            f"UPDATE golfers SET {set_clause} WHERE id=%s",
            (*updates.values(), req.golfer_id)
        )

    # Recalculate all team scores
    cur.execute("""
        SELECT t.*, u.username FROM teams t
        JOIN users u ON u.id = t.user_id
    """)
    teams_raw = cur.fetchall()
    all_teams = []
    for team in teams_raw:
        team_dict = dict(team)
        cur.execute("""
            SELECT g.* FROM golfers g
            JOIN team_golfers tg ON tg.golfer_id = g.id
            WHERE tg.team_id = %s
        """, (team_dict["id"],))
        team_dict["golfers"] = [dict(g) for g in cur.fetchall()]
        all_teams.append(team_dict)

    cur.execute("SELECT value FROM tournament_settings WHERE key='tournament_complete'")
    tc_row = cur.fetchone()
    tournament_complete = tc_row is not None and tc_row["value"] == "1"

    scores = calc_all_team_scores(all_teams, tournament_complete)
    for team_id, result in scores.items():
        cur.execute("""
            UPDATE teams SET final_score=%s, bonus_shots=%s, dk_total_points=%s
            WHERE id=%s
        """, (result["final"], result["bonus"], result["final"], team_id))

    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Golfer updated and team scores recalculated"}

@router.get("/users")
def list_users(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, phone, is_admin, created_at FROM users ORDER BY created_at")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return {"users": [dict(u) for u in users]}

@router.post("/set-round")
def set_round(round_num: int, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tournament_settings SET value=%s WHERE key='current_round'",
                (str(round_num),))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Current round set to {round_num}"}

@router.post("/set-tournament-complete")
def set_tournament_complete(complete: bool, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tournament_settings SET value=%s WHERE key='tournament_complete'",
        ("1" if complete else "0",)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Tournament marked complete." if complete else "Tournament marked in-progress."}

class DeleteTeamsRequest(BaseModel):
    team_ids: List[int]

@router.post("/delete-teams")
def delete_teams(req: DeleteTeamsRequest, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    if not req.team_ids:
        raise HTTPException(400, "No team IDs provided")
    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(req.team_ids))
    cur.execute(f"DELETE FROM team_golfers WHERE team_id IN ({placeholders})", req.team_ids)
    cur.execute(f"DELETE FROM teams WHERE id IN ({placeholders})", req.team_ids)
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"{deleted} team(s) deleted successfully", "deleted_count": deleted}

@router.post("/clear-teams")
def clear_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM team_golfers")
    cur.execute("DELETE FROM teams")
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "All teams cleared successfully"}

@router.post("/reset-golfers")
def reset_golfers(authorization: str = Header(None)):
    """Wipe the golfer field and all teams, then re-seed from db.py."""
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM team_golfers")
    cur.execute("DELETE FROM teams")
    cur.execute("DELETE FROM golfers")
    conn.commit()
    cur.close()
    conn.close()
    _seed_golfers()
    return {"message": "Golfer field reset and re-seeded. All teams cleared."}

@router.post("/clear-scores")
def clear_scores(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE golfers SET
            current_round=0,
            total_score=NULL,
            made_cut=1,
            finish_position=NULL,
            round1_score=NULL,
            round2_score=NULL,
            round3_score=NULL,
            round4_score=NULL,
            solo_leader_r1=0,
            solo_leader_r2=0,
            solo_leader_r3=0,
            solo_leader_r4=0
    """)
    cur.execute("UPDATE teams SET final_score=0, bonus_shots=0, dk_total_points=0")
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "All scores cleared successfully"}