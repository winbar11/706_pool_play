from fastapi import FastAPI
from fastapi.testclient import TestClient

from database.db import get_session
from database.models import TournamentSetting, User
from routers import admin as admin_router
from utils.auth_utils import create_token

app = FastAPI()
app.include_router(admin_router.router, prefix="/api/admin")
client = TestClient(app)


def make_admin(username="admin"):
    with get_session() as session:
        user = User(username=username, email=f"{username}@example.com",
                    password_hash="x", is_admin=1)
        session.add(user)
        session.flush()
        return user.id


def auth_header(user_id, username="admin"):
    return {"Authorization": f"Bearer {create_token(user_id, username, True)}"}


def seed_setting(key, value):
    with get_session() as session:
        session.add(TournamentSetting(key=key, value=value))


def test_lock_teams_writes_audit_entry():
    admin_id = make_admin()
    seed_setting("teams_locked", "0")

    resp = client.post("/api/admin/lock-teams", headers=auth_header(admin_id))
    assert resp.status_code == 200

    actions = client.get("/api/admin/actions", headers=auth_header(admin_id)).json()["actions"]
    assert len(actions) == 1
    assert actions[0]["action"] == "lock_teams"
    assert actions[0]["admin_username"] == "admin"


def test_set_paid_records_detail():
    admin_id = make_admin()
    target_id = make_admin("bob")

    resp = client.post(
        "/api/admin/set-paid", params={"user_id": target_id, "paid": True},
        headers=auth_header(admin_id),
    )
    assert resp.status_code == 200

    actions = client.get("/api/admin/actions", headers=auth_header(admin_id)).json()["actions"]
    action = next(a for a in actions if a["action"] == "set_paid")
    assert action["detail"] == {"user_id": target_id, "paid": True}


def test_actions_ordered_most_recent_first():
    admin_id = make_admin()
    seed_setting("teams_locked", "0")

    client.post("/api/admin/lock-teams", headers=auth_header(admin_id))
    client.post("/api/admin/unlock-teams", headers=auth_header(admin_id))

    actions = client.get("/api/admin/actions", headers=auth_header(admin_id)).json()["actions"]
    assert [a["action"] for a in actions] == ["unlock_teams", "lock_teams"]
