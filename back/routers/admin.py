from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from database.db import get_conn
from dependencies import get_admin_user
from scoring.scoring import calc_round_points, calc_total_points, calc_team_points
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
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    r = req.round_num

    cur.execute("SELECT * FROM golfers WHERE id=%s", (req.golfer_id,))
    golfer = cur.fetchone()
    if not golfer:
        cur.close()
        conn.close()
        raise HTTPException(404, "Golfer not found")

    round_pts = calc_round_points(
        req.birdies, req.eagles, req.bogeys, req.doubles,
        req.worse, req.pars, req.ace, req.double_eagle,
        req.bogey_free, req.birdie_streak
    )

    cur.execute(f"""
        UPDATE golfers SET
            r{r}_birdies=%s, r{r}_eagles=%s, r{r}_bogeys=%s, r{r}_doubles=%s,
            r{r}_worse=%s, r{r}_pars=%s, r{r}_ace=%s, r{r}_double_eagle=%s,
            r{r}_bogey_free=%s, r{r}_birdie_streak=%s,
            round{r}_score=%s, dk_r{r}_points=%s
        WHERE id=%s
    """, (req.birdies, req.eagles, req.bogeys, req.doubles,
            req.worse, req.pars, req.ace, req.double_eagle,
            req.bogey_free, req.birdie_streak,
            req.round_score, round_pts, req.golfer_id))

    cur.execute("SELECT * FROM golfers WHERE id=%s", (req.golfer_id,))
    updated = dict(cur.fetchone())
    total = calc_total_points(updated)
    cur.execute("UPDATE golfers SET dk_total_points=%s WHERE id=%s",
                (total, req.golfer_id))

    cur.execute("""
        SELECT t.* FROM teams t
        JOIN team_golfers tg ON tg.team_id = t.id
        WHERE tg.golfer_id = %s
    """, (req.golfer_id,))
    teams = cur.fetchall()

    for team in teams:
        cur.execute("""
            SELECT g.* FROM golfers g
            JOIN team_golfers tg ON tg.golfer_id = g.id
            WHERE tg.team_id = %s
        """, (team["id"],))
        golfers = cur.fetchall()
        total_pts = calc_team_points([dict(g) for g in golfers])
        cur.execute("UPDATE teams SET dk_total_points=%s WHERE id=%s",
                    (total_pts, team["id"]))

    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Golfer updated. Round {r} DK pts: {round_pts}"}

@router.get("/users")
def list_users(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at")
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

@router.post("/clear-scores")
def clear_scores(authorization: str = Header(None)):
    get_admin_user(authorization=authorization)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE golfers SET
            current_round=0, total_score=NULL, made_cut=1, finish_position=NULL,
            round1_score=NULL, round2_score=NULL, round3_score=NULL, round4_score=NULL,
            dk_r1_points=0, dk_r2_points=0, dk_r3_points=0, dk_r4_points=0,
            dk_total_points=0,
            r1_birdies=0, r1_eagles=0, r1_bogeys=0, r1_doubles=0, r1_worse=0,
            r1_pars=0, r1_ace=0, r1_double_eagle=0, r1_bogey_free=0, r1_birdie_streak=0,
            r2_birdies=0, r2_eagles=0, r2_bogeys=0, r2_doubles=0, r2_worse=0,
            r2_pars=0, r2_ace=0, r2_double_eagle=0, r2_bogey_free=0, r2_birdie_streak=0,
            r3_birdies=0, r3_eagles=0, r3_bogeys=0, r3_doubles=0, r3_worse=0,
            r3_pars=0, r3_ace=0, r3_double_eagle=0, r3_bogey_free=0, r3_birdie_streak=0,
            r4_birdies=0, r4_eagles=0, r4_bogeys=0, r4_doubles=0, r4_worse=0,
            r4_pars=0, r4_ace=0, r4_double_eagle=0, r4_bogey_free=0, r4_birdie_streak=0,
            all4_under70=0
    """)
    cur.execute("UPDATE teams SET dk_total_points=0")
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "All scores cleared successfully"}