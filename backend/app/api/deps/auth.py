"""`get_current_user` dependency that protects every v1 router.

Reads the Authorization: Bearer <token> header, verifies via the configured
auth provider, returns a Principal. The Principal can be ignored by endpoints
that just need "any logged-in user" — they take it via Depends(require_user).

Set `AUTH_DISABLED=true` to short-circuit auth for local dev — the dependency
returns a synthetic Principal so existing integration code keeps working
without a real signup. Production deployments should leave this false.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.auth import get_provider
from app.services.auth.base import AuthError, Principal

_DEV_PRINCIPAL = Principal(user_id="dev-anonymous", email="[email protected]", is_admin=True)


async def require_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    if settings.auth_disabled:
        return _DEV_PRINCIPAL

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = parts[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empty bearer token")

    try:
        principal = await get_provider().verify_token(db, token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal


async def require_admin(principal: Principal = Depends(require_user)) -> Principal:
    if not principal.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return principal
