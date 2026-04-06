from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database.db import get_conn
from utils.auth_utils import hash_password, verify_password, create_token
from dependencies import get_current_user

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    phone: str = None

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
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username=%s OR email=%s",
        (req.username.lower(), req.email.lower())
    )
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        raise HTTPException(400, "Username or email already taken")

    pw_hash = hash_password(req.password)

    cur.execute("SELECT COUNT(*) as n FROM users")
    count = cur.fetchone()["n"]
    is_admin = 1 if count == 0 else 0

    cur.execute(
        "INSERT INTO users (username, email, password_hash, is_admin, phone) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (req.username.lower(), req.email.lower(), pw_hash, is_admin, req.phone)
    )
    user_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()

    token = create_token(user_id, req.username.lower(), bool(is_admin))
    return {"token": token, "username": req.username.lower(),
            "is_admin": bool(is_admin), "user_id": user_id}

@router.post("/login")
def login(req: LoginRequest):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s", (req.username.lower(),))
    user = cur.fetchone()
    cur.close()
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