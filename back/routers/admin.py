from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from database.db import get_conn
from dependencies import get_admin_user
from scoring.scoring import calc_round_points, calc_total_points, calc_team_points
import asyncio

router = APIRouter()

@router.post("/lock-teams")
def lock_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    conn.execute("UPDATE tournament_settings SET value='1' WHERE key='teams_locked'")
    conn.commit()
    conn.close()
    return {"message": "Teams locked. No more changes allowed."}

@router.post("/unlock-teams")
def unlock_teams(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    conn.execute("UPDATE tournament_settings SET value='0' WHERE key='teams_locked'")
    conn.commit()
    conn.close()
    return {"message": "Teams unlocked."}

@router.post("/refresh-scores")
async def trigger_refresh(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    from scheduler import refresh_scores
    asyncio.create_task(refresh_scores())
    return {"message": "Score refresh triggered (running in background)"}

class ManualGolferUpdate(BaseModel):
    golfer_id: int
    round_num: int
    birdies: int = 0
    eagles: int = 0
    bogeys: int = 0
    doubles: int = 0
    worse: int = 0
    pars: int = 0
    ace: int = 0
    double_eagle: int = 0
    bogey_free: int = 0
    birdie_streak: int = 0
    round_score: int = None

@router.post("/update-golfer")
def manual_update_golfer(req: ManualGolferUpdate, authorization: str = Header(None)):
    """Manual fallback if ESPN API is unavailable."""
    get_admin_user(authorization=authorization)
    conn = get_conn()
    r = req.round_num
    golfer = conn.execute("SELECT * FROM golfers WHERE id=?", (req.golfer_id,)).fetchone()
    if not golfer:
        conn.close()
        raise HTTPException(404, "Golfer not found")

    from scoring import calc_round_points, calc_total_points
    round_pts = calc_round_points(
        req.birdies, req.eagles, req.bogeys, req.doubles,
        req.worse, req.pars, req.ace, req.double_eagle,
        req.bogey_free, req.birdie_streak
    )

    conn.execute(f"""
        UPDATE golfers SET
            r{r}_birdies=?, r{r}_eagles=?, r{r}_bogeys=?, r{r}_doubles=?,
            r{r}_worse=?, r{r}_pars=?, r{r}_ace=?, r{r}_double_eagle=?,
            r{r}_bogey_free=?, r{r}_birdie_streak=?,
            round{r}_score=?, dk_r{r}_points=?
        WHERE id=?
    """, (req.birdies, req.eagles, req.bogeys, req.doubles,
            req.worse, req.pars, req.ace, req.double_eagle,
            req.bogey_free, req.birdie_streak,
            req.round_score, round_pts, req.golfer_id))

    # Recompute total
    updated = dict(conn.execute("SELECT * FROM golfers WHERE id=?",
                                (req.golfer_id,)).fetchone())
    total = calc_total_points(updated)
    conn.execute("UPDATE golfers SET dk_total_points=? WHERE id=?",
                (total, req.golfer_id))

    # Recompute all teams containing this golfer
    teams = conn.execute("""
        SELECT t.* FROM teams t
        JOIN team_golfers tg ON tg.team_id = t.id
        WHERE tg.golfer_id = ?
    """, (req.golfer_id,)).fetchall()

    for team in teams:
        golfers = conn.execute("""
            SELECT g.* FROM golfers g
            JOIN team_golfers tg ON tg.golfer_id = g.id
            WHERE tg.team_id = ?
        """, (team["id"],)).fetchall()
        total_pts = calc_team_points([dict(g) for g in golfers])
        conn.execute("UPDATE teams SET dk_total_points=? WHERE id=?",
                    (total_pts, team["id"]))

    conn.commit()
    conn.close()
    return {"message": f"Golfer updated. Round {r} DK pts: {round_pts}"}

@router.get("/users")
def list_users(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    users = conn.execute(
        "SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at"
    ).fetchall()
    conn.close()
    return {"users": [dict(u) for u in users]}

@router.post("/set-round")
def set_round(round_num: int, authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    conn.execute("UPDATE tournament_settings SET value=? WHERE key='current_round'",
                (str(round_num),))
    conn.commit()
    conn.close()
    return {"message": f"Current round set to {round_num}"}