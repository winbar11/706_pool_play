from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database.db import get_conn
from utils.auth_utils import hash_password, verify_password, create_token
from dependencies import get_current_user
from fastapi import Header

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if len(req.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")

    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM users WHERE username=? OR email=?",
        (req.username.lower(), req.email.lower())
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Username or email already taken")

    pw_hash = hash_password(req.password)
    # First user is auto-admin
    count = conn.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
    is_admin = 1 if count == 0 else 0

    cur = conn.execute(
        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?,?,?,?)",
        (req.username.lower(), req.email.lower(), pw_hash, is_admin)
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    token = create_token(user_id, req.username.lower(), bool(is_admin))
    return {"token": token, "username": req.username.lower(),
            "is_admin": bool(is_admin), "user_id": user_id}

@router.post("/login")
def login(req: LoginRequest):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username=?", (req.username.lower(),)
    ).fetchone()
    conn.close()
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    token = create_token(user["id"], user["username"], bool(user["is_admin"]))
    return {"token": token, "username": user["username"],
            "is_admin": bool(user["is_admin"]), "user_id": user["id"]}

@router.get("/me")
def me(authorization: str = Header(None)):
    user = get_current_user(authorization)
    return {"username": user["username"], "is_admin": bool(user["is_admin"]),
            "user_id": user["id"], "email": user["email"]}