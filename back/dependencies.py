from fastapi import HTTPException, Header
from utils.auth_utils import decode_token
from database.db import get_conn

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (payload["sub"],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)

def get_admin_user(authorization: str = Header(None)):
    u = get_current_user(authorization)
    if not u["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return u