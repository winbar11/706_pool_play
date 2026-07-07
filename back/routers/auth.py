import secrets
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import func, select
from database.db import get_session
from database.models import PasswordResetToken, User
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

    username = req.username.lower()
    email = req.email.lower()

    with get_session() as session:
        existing = session.execute(
            select(User).where((User.username == username) | (User.email == email))
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(400, "Username or email already taken")

        pw_hash = hash_password(req.password)
        count = session.query(User).count()
        is_admin = 1 if count == 0 else 0

        user = User(
            username=username, email=email, password_hash=pw_hash,
            is_admin=is_admin, phone=req.phone,
        )
        session.add(user)
        session.flush()
        user_id = user.id

    token = create_token(user_id, username, bool(is_admin))
    return {"token": token, "username": username,
            "is_admin": bool(is_admin), "user_id": user_id}

@router.post("/login")
def login(req: LoginRequest):
    with get_session() as session:
        user = session.execute(
            select(User).where(User.username == req.username.lower())
        ).scalar_one_or_none()

        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(401, "Invalid username or password")

        token = create_token(user.id, user.username, bool(user.is_admin))
        return {"token": token, "username": user.username,
                "is_admin": bool(user.is_admin), "user_id": user.id}

@router.get("/me")
def me(authorization: str = Header(None)):
    user = get_current_user(authorization)
    return {"username": user["username"], "is_admin": bool(user["is_admin"]),
            "user_id": user["id"], "email": user["email"]}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    with get_session() as session:
        user = session.execute(
            select(User).where(User.email == req.email.lower().strip())
        ).scalar_one_or_none()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            for old_token in session.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used == 0,
                )
            ).scalars():
                old_token.used = 1

            session.add(PasswordResetToken(token=token, user_id=user.id, expires_at=expires_at))
            session.flush()

            try:
                send_reset_email(user.email, token)
            except Exception as e:
                logger.error("Reset email failed for user %s: %s", user.id, e)

    # Always return the same message to prevent email enumeration
    return {"message": "If that email is registered, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    with get_session() as session:
        row = session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == req.token,
                PasswordResetToken.used == 0,
                PasswordResetToken.expires_at > func.now(),
            )
        ).scalar_one_or_none()

        if not row:
            raise HTTPException(400, "Reset link is invalid or has expired")

        user = session.get(User, row.user_id)
        user.password_hash = hash_password(req.password)
        row.used = 1

    return {"message": "Password updated successfully. You can now log in."}
