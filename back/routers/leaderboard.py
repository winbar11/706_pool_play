from fastapi import APIRouter
from database.db import get_conn


router = APIRouter()

def fmt_score(score):
    if score is None:
        return "—"
    if score == 0:
        return "E"
    return f"+{score}" if score > 0 else str(score)

@router.get("")
def leaderboard():
    conn = get_conn()
    cur  = conn.cursor()

    cur.execute("""
        SELECT t.id, t.team_name, t.total_salary,
                t.final_score, t.bonus_shots, t.dk_total_points,
                t.is_locked, u.username
        FROM teams t
        JOIN users u ON u.id = t.user_id
        ORDER BY t.final_score ASC NULLS LAST
    """)
    teams = cur.fetchall()

    result = []
    rank = 1
    for i, team in enumerate(teams):
        cur.execute("""
            SELECT g.id, g.name, g.salary, g.world_rank,
                    g.current_round, g.total_score, g.made_cut,
                    g.finish_position,
                    g.round1_score, g.round2_score,
                    g.round3_score, g.round4_score,
                    g.solo_leader_r1, g.solo_leader_r2,
                    g.solo_leader_r3, g.solo_leader_r4
            FROM golfers g
            JOIN team_golfers tg ON tg.golfer_id = g.id
            WHERE tg.team_id = %s
            ORDER BY g.total_score ASC NULLS LAST
        """, (team["id"],))
        golfers = cur.fetchall()

        # Assign tied rank: same score as previous team keeps the same rank
        if i > 0 and team["final_score"] == teams[i - 1]["final_score"]:
            rank = result[-1]["rank"]
        else:
            rank = i + 1

        result.append({
            **dict(team),
            "rank":        rank,
            "final_score": team["final_score"],
            "bonus_shots": team["bonus_shots"],
            "golfers":     [dict(g) for g in golfers]
        })

    cur.execute("SELECT key, value FROM tournament_settings")
    settings = cur.fetchall()
    cur.close()
    conn.close()

    s = {r["key"]: r["value"] for r in settings}
    return {"teams": result, "settings": s}