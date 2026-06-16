from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database.db import get_conn
from dependencies import get_current_user

router = APIRouter()

SALARY_CAP = 50000
ROSTER_SIZE = 6
MAX_TEAMS = 1

class TeamSubmit(BaseModel):
    team_name: str
    golfer_ids: list[int]
    team_id: int | None = None

@router.post("/submit")
def submit_team(req: TeamSubmit, authorization: str = Header(None)):
    user = get_current_user(authorization)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT value FROM tournament_settings WHERE key='teams_locked'")
    locked = cur.fetchone()
    if locked and locked["value"] == "1":
        cur.close()
        conn.close()
        raise HTTPException(400, "Tournament has started — teams are locked")

    if len(req.golfer_ids) != ROSTER_SIZE:
        cur.close()
        conn.close()
        raise HTTPException(400, f"Must select exactly {ROSTER_SIZE} golfers")

    if len(set(req.golfer_ids)) != ROSTER_SIZE:
        cur.close()
        conn.close()
        raise HTTPException(400, "Duplicate golfers not allowed")

    golfers = []
    for gid in req.golfer_ids:
        cur.execute("SELECT * FROM golfers WHERE id=%s", (gid,))
        g = cur.fetchone()
        if not g:
            cur.close()
            conn.close()
            raise HTTPException(404, f"Golfer id {gid} not found")
        golfers.append(dict(g))

    total_salary = sum(g["salary"] for g in golfers)
    if total_salary > SALARY_CAP:
        cur.close()
        conn.close()
        raise HTTPException(400,
            f"Salary cap exceeded: ${total_salary:,} > ${SALARY_CAP:,}")

    if req.team_id is not None:
        # Update existing team — verify ownership
        cur.execute("SELECT id FROM teams WHERE id=%s AND user_id=%s", (req.team_id, user["id"]))
        existing = cur.fetchone()
        if not existing:
            cur.close()
            conn.close()
            raise HTTPException(404, "Team not found")
        cur.execute("DELETE FROM team_golfers WHERE team_id=%s", (req.team_id,))
        cur.execute(
            "UPDATE teams SET team_name=%s, total_salary=%s WHERE id=%s",
            (req.team_name, total_salary, req.team_id)
        )
        team_id = req.team_id
    else:
        # Create new team — enforce per-user cap
        cur.execute("SELECT COUNT(*) as cnt FROM teams WHERE user_id=%s", (user["id"],))
        count = cur.fetchone()["cnt"]
        if count >= MAX_TEAMS:
            cur.close()
            conn.close()
            raise HTTPException(400, f"You may have at most {MAX_TEAMS} teams")
        cur.execute(
            """INSERT INTO teams (user_id, team_name, total_salary, final_score, bonus_shots, dk_total_points)
                VALUES (%s, %s, %s, 0, 0, 0) RETURNING id""",
            (user["id"], req.team_name, total_salary)
        )
        team_id = cur.fetchone()["id"]

    for gid in req.golfer_ids:
        cur.execute("INSERT INTO team_golfers (team_id, golfer_id) VALUES (%s,%s)",
                    (team_id, gid))

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Team submitted successfully", "team_id": team_id,
            "total_salary": total_salary}

@router.get("/my")
def my_teams(authorization: str = Header(None)):
    user = get_current_user(authorization)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM teams WHERE user_id=%s ORDER BY id ASC", (user["id"],))
    teams = cur.fetchall()

    result = []
    for team in teams:
        cur.execute("""
            SELECT g.* FROM golfers g
            JOIN team_golfers tg ON tg.golfer_id = g.id
            WHERE tg.team_id = %s
            ORDER BY g.total_score ASC NULLS LAST
        """, (team["id"],))
        golfers = cur.fetchall()
        result.append({**dict(team), "golfers": [dict(g) for g in golfers]})

    cur.close()
    conn.close()
    return {"teams": result}

@router.get("/{team_id}")
def get_team(team_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM teams WHERE id=%s", (team_id,))
    team = cur.fetchone()
    if not team:
        cur.close()
        conn.close()
        raise HTTPException(404, "Team not found")

    cur.execute("""
        SELECT g.* FROM golfers g
        JOIN team_golfers tg ON tg.golfer_id = g.id
        WHERE tg.team_id = %s
        ORDER BY g.total_score ASC NULLS LAST
    """, (team_id,))
    golfers = cur.fetchall()
    cur.close()
    conn.close()
    return {**dict(team), "golfers": [dict(g) for g in golfers]}
