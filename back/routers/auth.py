import secrets
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database.db import get_conn
from utils.auth_utils import hash_password, verify_password, create_token, send_reset_email
from dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    phone: str = None

class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
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

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, email FROM users WHERE email=%s", (req.email.lower().strip(),))
    user = cur.fetchone()

    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        cur.execute(
            "UPDATE password_reset_tokens SET used=1 WHERE user_id=%s AND used=0",
            (user["id"],)
        )
        cur.execute(
            "INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (%s, %s, %s)",
            (token, user["id"], expires_at)
        )
        conn.commit()

        try:
            send_reset_email(user["email"], token)
        except Exception as e:
            logger.error("Reset email failed for user %s: %s", user["id"], e)

    cur.close()
    conn.close()
    # Always return the same message to prevent email enumeration
    return {"message": "If that email is registered, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id FROM password_reset_tokens
        WHERE token=%s AND used=0 AND expires_at > NOW()
    """, (req.token,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        raise HTTPException(400, "Reset link is invalid or has expired")

    pw_hash = hash_password(req.password)
    cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (pw_hash, row["user_id"]))
    cur.execute("UPDATE password_reset_tokens SET used=1 WHERE token=%s", (req.token,))
    conn.commit()

    cur.close()
    conn.close()
    return {"message": "Password updated successfully. You can now log in."}
