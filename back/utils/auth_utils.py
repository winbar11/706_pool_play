import os
import hashlib
import hmac
import secrets
import time
import json
import base64
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. A random key must never be "
        "generated as a fallback — every process restart or extra worker would get "
        "a different key, silently invalidating all issued tokens and rejecting "
        "tokens issued by other instances."
    )
TOKEN_EXPIRE_SECONDS = 60 * 60 * 24  # 24 hours — bounds the window a leaked token stays valid

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}:{h.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(h, check.hex())
    except Exception:
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))

def create_token(user_id: int, username: str, is_admin: bool) -> str:
    payload = {"sub": user_id, "usr": username, "adm": is_admin,
                "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS}
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body   = _b64(json.dumps(payload).encode())
    sig    = _b64(hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(),
                            hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"

def decode_token(token: str) -> dict | None:
    try:
        header, body, sig = token.split(".")
        expected = _b64(hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(),
                                hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_unb64(body))
        if payload["exp"] < time.time():
            return None
        return payload
    except Exception:
        return None

def send_reset_email(to_email: str, token: str) -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")

    if not smtp_host or not smtp_user:
        logger.warning("SMTP not configured — skipping reset email to %s", to_email)
        return False

    reset_url = f"{frontend_url}/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "706 Masters Pool — Reset Your Password"
    msg["From"] = smtp_from
    msg["To"] = to_email

    text = (
        f"Reset your 706 Masters Pool password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in 1 hour. If you didn't request this, ignore this email."
    )
    html = f"""<div style="font-family:sans-serif;max-width:480px;margin:0 auto">
  <h2 style="color:#1a3a1a">706 Masters Pool</h2>
  <p>You requested a password reset. Click the button below to set a new password:</p>
  <p>
    <a href="{reset_url}"
       style="display:inline-block;padding:12px 24px;background:#2d6a2d;
              color:#fff;text-decoration:none;border-radius:6px;font-weight:bold">
      Reset Password
    </a>
  </p>
  <p style="color:#666;font-size:0.88em">Or copy this link:<br>{reset_url}</p>
  <p style="color:#666;font-size:0.88em">
    This link expires in <strong>1 hour</strong>.
    If you didn't request this, you can safely ignore this email.
  </p>
</div>"""

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_from, [to_email], msg.as_string())

    return True
