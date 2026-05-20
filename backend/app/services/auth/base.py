from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@dataclass
class Principal:
    """Identity attached to a request after successful auth."""

    user_id: str
    email: str
    is_admin: bool


class AuthError(Exception):
    """Raised for any auth failure (bad creds, expired token, etc.)."""


class AuthProvider(Protocol):
    name: str

    async def register(self, db: AsyncSession, *, email: str, password: str, name: str | None) -> User: ...

    async def signin(self, db: AsyncSession, *, email: str, password: str) -> tuple[User, str, int]:
        """Returns (user, access_token, expires_in_seconds)."""
        ...

    async def verify_token(self, db: AsyncSession, token: str) -> Principal: ...
