from datetime import datetime, timedelta, timezone
from typing import Any
import base64
import bcrypt
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": subject, "exp": expires, "type": "access"}, settings.secret_key, algorithm="HS256")


def create_refresh_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    return jwt.encode({"sub": subject, "exp": expires, "type": "refresh"}, settings.secret_key, algorithm="HS256")


def decode_token(token: str, token_type: str = "access") -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if payload.get("type") != token_type:
        raise JWTError("Invalid token type")
    return payload


def get_fernet() -> Fernet:
    if settings.encryption_key:
        try:
            return Fernet(settings.encryption_key.encode())
        except Exception:
            pass
    # Development fallback is derived deterministically. Production must set ENCRYPTION_KEY.
    key = base64.urlsafe_b64encode(hashlib.sha256(b"your_stable_development_key").digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return get_fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        raise ValueError("Unable to decrypt stored credential")
