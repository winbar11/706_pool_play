from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database.db import get_conn
from dependencies import get_current_user
from scoring.scoring import calc_team_points

router = APIRouter()

SALARY_CAP = 50000
ROSTER_SIZE = 6

class TeamSubmit(BaseModel):
    team_name: str
    golfer_ids: list[int]

@router.post("/submit")
def submit_team(req: TeamSubmit, authorization: str = Header(None)):
    user = get_current_user(authorization)
    conn = get_conn()

    # Check if teams are locked
    locked = conn.execute(
        "SELECT value FROM tournament_settings WHERE key='teams_locked'"
    ).fetchone()
    if locked and locked["value"] == "1":
        conn.close()
        raise HTTPException(400, "Tournament has started — teams are locked")

    if len(req.golfer_ids) != ROSTER_SIZE:
        conn.close()
        raise HTTPException(400, f"Must select exactly {ROSTER_SIZE} golfers")

    if len(set(req.golfer_ids)) != ROSTER_SIZE:
        conn.close()
        raise HTTPException(400, "Duplicate golfers not allowed")

    # Validate golfers + salary cap
    golfers = []
    for gid in req.golfer_ids:
        g = conn.execute("SELECT * FROM golfers WHERE id=?", (gid,)).fetchone()
        if not g:
            conn.close()
            raise HTTPException(404, f"Golfer id {gid} not found")
        golfers.append(dict(g))

    total_salary = sum(g["salary"] for g in golfers)
    if total_salary > SALARY_CAP:
        conn.close()
        raise HTTPException(400,
            f"Salary cap exceeded: ${total_salary:,} > ${SALARY_CAP:,}")

    # Delete existing team if any
    existing = conn.execute(
        "SELECT id FROM teams WHERE user_id=?", (user["id"],)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM team_golfers WHERE team_id=?", (existing["id"],))
        conn.execute("DELETE FROM teams WHERE id=?", (existing["id"],))

    # Insert new team
    dk_pts = calc_team_points(golfers)
    cur = conn.execute(
        "INSERT INTO teams (user_id, team_name, total_salary, dk_total_points) VALUES (?,?,?,?)",
        (user["id"], req.team_name, total_salary, dk_pts)
    )
    team_id = cur.lastrowid
    for gid in req.golfer_ids:
        conn.execute("INSERT INTO team_golfers (team_id, golfer_id) VALUES (?,?)",
                     (team_id, gid))

    conn.commit()
    conn.close()
    return {"message": "Team submitted successfully", "team_id": team_id,
            "total_salary": total_salary, "dk_total_points": dk_pts}

@router.get("/my")
def my_team(authorization: str = Header(None)):
    user = get_current_user(authorization)
    conn = get_conn()
    team = conn.execute(
        "SELECT * FROM teams WHERE user_id=?", (user["id"],)
    ).fetchone()
    if not team:
        conn.close()
        return {"team": None}

    golfers = conn.execute("""
        SELECT g.* FROM golfers g
        JOIN team_golfers tg ON tg.golfer_id = g.id
        WHERE tg.team_id = ?
        ORDER BY g.dk_total_points DESC
    """, (team["id"],)).fetchall()
    conn.close()
    return {
        "team": {**dict(team), "golfers": [dict(g) for g in golfers]}
    }

@router.get("/{team_id}")
def get_team(team_id: int):
    conn = get_conn()
    team = conn.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()
    if not team:
        conn.close()
        raise HTTPException(404, "Team not found")
    golfers = conn.execute("""
        SELECT g.* FROM golfers g
        JOIN team_golfers tg ON tg.golfer_id = g.id
        WHERE tg.team_id = ?
        ORDER BY g.dk_total_points DESC
    """, (team_id,)).fetchall()
    conn.close()
    return {**dict(team), "golfers": [dict(g) for g in golfers]}