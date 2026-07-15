from fastapi import FastAPI
from fastapi.testclient import TestClient

from database.db import get_session
from database.models import Golfer, TournamentSetting, User
from routers import teams as teams_router
from utils.auth_utils import create_token

app = FastAPI()
app.include_router(teams_router.router, prefix="/api/teams")
client = TestClient(app)


def make_user(username="alice"):
    with get_session() as session:
        user = User(username=username, email=f"{username}@example.com",
                    password_hash="x", is_admin=0)
        session.add(user)
        session.flush()
        return user.id


def make_golfers(count, salary):
    ids = []
    with get_session() as session:
        for i in range(count):
            g = Golfer(name=f"Golfer {i}", salary=salary)
            session.add(g)
            session.flush()
            ids.append(g.id)
    return ids


def auth_header(user_id, username="alice"):
    return {"Authorization": f"Bearer {create_token(user_id, username, False)}"}


def submit(golfer_ids, user_id, team_name="Team A", team_id=None):
    return client.post("/api/teams/submit", json={
        "team_name": team_name, "golfer_ids": golfer_ids, "team_id": team_id,
    }, headers=auth_header(user_id))


def test_submit_team_success_within_cap():
    user_id = make_user()
    golfer_ids = make_golfers(6, salary=8000)  # 48,000 total, under the 50k cap

    resp = submit(golfer_ids, user_id)

    assert resp.status_code == 200
    assert resp.json()["total_salary"] == 48000


def test_submit_team_rejects_wrong_roster_size():
    user_id = make_user()
    golfer_ids = make_golfers(5, salary=5000)

    resp = submit(golfer_ids, user_id)

    assert resp.status_code == 400
    assert "exactly 6 golfers" in resp.json()["detail"]


def test_submit_team_rejects_duplicate_golfers():
    user_id = make_user()
    golfer_ids = make_golfers(5, salary=5000)
    golfer_ids.append(golfer_ids[0])  # 6 ids, but a duplicate

    resp = submit(golfer_ids, user_id)

    assert resp.status_code == 400
    assert "Duplicate" in resp.json()["detail"]


def test_submit_team_rejects_salary_cap_exceeded():
    user_id = make_user()
    golfer_ids = make_golfers(6, salary=9000)  # 54,000 total, over the 50k cap

    resp = submit(golfer_ids, user_id)

    assert resp.status_code == 400
    assert "Salary cap exceeded" in resp.json()["detail"]


def test_submit_team_rejects_unknown_golfer_id():
    user_id = make_user()
    golfer_ids = make_golfers(5, salary=5000)
    golfer_ids.append(999999)

    resp = submit(golfer_ids, user_id)

    assert resp.status_code == 404


def test_submit_team_rejects_when_tournament_locked():
    user_id = make_user()
    golfer_ids = make_golfers(6, salary=8000)
    with get_session() as session:
        session.add(TournamentSetting(key="teams_locked", value="1"))

    resp = submit(golfer_ids, user_id)

    assert resp.status_code == 400
    assert "locked" in resp.json()["detail"]


def test_submit_team_enforces_max_teams_per_user():
    user_id = make_user()
    first_ids = make_golfers(6, salary=8000)
    second_ids = make_golfers(6, salary=7000)

    first = submit(first_ids, user_id, team_name="Team A")
    assert first.status_code == 200

    second = submit(second_ids, user_id, team_name="Team B")

    assert second.status_code == 400
    assert "at most 1 teams" in second.json()["detail"]


def test_update_existing_team_rejects_non_owner():
    owner_id = make_user("alice")
    other_id = make_user("bob")
    golfer_ids = make_golfers(6, salary=8000)

    created = submit(golfer_ids, owner_id)
    team_id = created.json()["team_id"]

    resp = submit(golfer_ids, other_id, team_name="Hijacked", team_id=team_id)

    assert resp.status_code == 404
