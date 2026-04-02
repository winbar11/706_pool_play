from fastapi import APIRouter
from database.db import get_conn

router = APIRouter()

@router.get("")
def list_golfers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, salary, world_rank, country,
                current_round, total_score, made_cut, finish_position,
                dk_total_points, dk_r1_points, dk_r2_points, dk_r3_points, dk_r4_points,
                round1_score, round2_score, round3_score, round4_score
        FROM golfers
        ORDER BY salary DESC
    """)
    golfers = cur.fetchall()
    cur.close()
    conn.close()
    return {"golfers": [dict(g) for g in golfers]}