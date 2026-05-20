"""Local auth provider — bcrypt password hashing + HS256 JWTs we sign ourselves."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.auth.base import AuthError, AuthProvider, Principal

_JWT_ALG = "HS256"


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, AttributeError):
        return False


def _make_token(user: User) -> tuple[str, int]:
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "iss": "dclaw-crisis",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALG)
    return token, expires_in


class LocalProvider:
    name = "local"

    async def register(self, db: AsyncSession, *, email: str, password: str, name: str | None) -> User:
        repo = UserRepository(db)
        existing = await repo.get_by_email(email)
        if existing is not None:
            raise AuthError("Email already registered")
        user = User(
            email=email.lower(),
            name=name,
            password_hash=_hash_password(password),
            auth_provider=self.name,
        )
        return await repo.create(user)

    async def signin(self, db: AsyncSession, *, email: str, password: str) -> tuple[User, str, int]:
        repo = UserRepository(db)
        user = await repo.get_by_email(email)
        if user is None or not user.is_active or user.password_hash is None:
            raise AuthError("Invalid email or password")
        if not _verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")
        token, expires_in = _make_token(user)
        return user, token, expires_in

    async def verify_token(self, db: AsyncSession, token: str) -> Principal:
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[_JWT_ALG], options={"require": ["sub", "exp"]}
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError(f"Invalid token: {exc}") from exc

        user_id = payload.get("sub")
        email = payload.get("email", "")
        is_admin = bool(payload.get("is_admin", False))
        if not user_id:
            raise AuthError("Token missing subject")
        return Principal(user_id=user_id, email=email, is_admin=is_admin)
