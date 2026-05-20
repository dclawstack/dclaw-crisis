"""Logto auth provider — stub.

When wired, this provider will:
- redirect users to Logto's hosted sign-in UI (no /signup or /signin on our side)
- accept JWTs issued by Logto via the Authorization header
- verify them against Logto's JWKS endpoint
- look up or auto-create a local User row keyed by Logto's `sub` claim

For now it raises NotImplementedError, which is intentional — switching
AUTH_PROVIDER=logto without configuring Logto credentials should fail loudly,
not silently degrade to no-auth.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth.base import AuthError, Principal


class LogtoProvider:
    name = "logto"

    async def register(self, db: AsyncSession, *, email: str, password: str, name: str | None) -> User:
        raise AuthError("Sign-up via Logto: redirect users to the Logto hosted sign-up UI (not implemented here).")

    async def signin(self, db: AsyncSession, *, email: str, password: str) -> tuple[User, str, int]:
        raise AuthError("Sign-in via Logto: redirect users to the Logto hosted sign-in UI (not implemented here).")

    async def verify_token(self, db: AsyncSession, token: str) -> Principal:
        raise NotImplementedError(
            "LogtoProvider.verify_token is not implemented yet. Wire JWKS verification against the configured Logto endpoint."
        )
