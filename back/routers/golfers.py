from fastapi import APIRouter
from database.db import get_session
from database.models import Golfer

router = APIRouter()

_FIELDS = [
    "id", "name", "salary", "world_rank", "country",
    "current_round", "total_score", "made_cut", "finish_position",
    "round1_score", "round2_score", "round3_score", "round4_score",
    "solo_leader_r1", "solo_leader_r2", "solo_leader_r3", "solo_leader_r4",
]

@router.get("")
def list_golfers():
    with get_session() as session:
        golfers = session.query(Golfer).order_by(Golfer.salary.desc()).all()
        return {"golfers": [{f: getattr(g, f) for f in _FIELDS} for g in golfers]}
