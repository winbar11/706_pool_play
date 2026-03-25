from fastapi import APIRouter
from database.db import get_conn

router = APIRouter()

@router.get("")
def leaderboard():
    conn = get_conn()
    teams = conn.execute("""
        SELECT t.id, t.team_name, t.total_salary, t.dk_total_points,
            t.is_locked, u.username
        FROM teams t
        JOIN users u ON u.id = t.user_id
        ORDER BY t.dk_total_points DESC
    """).fetchall()

    result = []
    for i, team in enumerate(teams):
        golfers = conn.execute("""
            SELECT g.id, g.name, g.salary, g.dk_total_points,
                    g.current_round, g.total_score, g.made_cut,
                    g.finish_position, g.world_rank,
                    g.dk_r1_points, g.dk_r2_points, g.dk_r3_points, g.dk_r4_points
            FROM golfers g
            JOIN team_golfers tg ON tg.golfer_id = g.id
            WHERE tg.team_id = ?
            ORDER BY g.dk_total_points DESC
        """, (team["id"],)).fetchall()
        result.append({
            **dict(team),
            "rank": i + 1,
            "golfers": [dict(g) for g in golfers]
        })

    settings = conn.execute("SELECT key, value FROM tournament_settings").fetchall()
    conn.close()
    s = {r["key"]: r["value"] for r in settings}
    return {"teams": result, "settings": s}