from jose import JWTError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, username: str, email: str, password: str) -> User:
        existing = self.db.query(User).filter(or_(User.username == username, User.email == email)).first()
        if existing:
            raise ConflictError("Username or email already exists")
        user = User(username=username, email=email, password_hash=hash_password(password), is_active=True)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self.db.query(User).filter(User.email == email).first()
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        return create_access_token(str(user.id)), create_refresh_token(str(user.id))

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token, "refresh")
            user_id = int(payload["sub"])
        except (JWTError, KeyError, ValueError):
            raise AuthenticationError("Invalid or expired refresh token")
        if self.db.get(User, user_id) is None:
            raise AuthenticationError("Unknown user")
        return create_access_token(str(user_id)), create_refresh_token(str(user_id))
