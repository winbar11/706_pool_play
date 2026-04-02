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
                round1_score, round2_score, round3_score, round4_score,
                solo_leader_r1, solo_leader_r2, solo_leader_r3, solo_leader_r4
        FROM golfers
        ORDER BY salary DESC
    """)
    golfers = cur.fetchall()
    cur.close()
    conn.close()
    return {"golfers": [dict(g) for g in golfers]}