from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_user
from app.core.database import get_db
from app.core.rate_limit import (
    assert_signin_allowed,
    clear_signin_failures,
    ip_limit,
    register_signin_failure,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    SigninRequest,
    SigninResponse,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import get_provider
from app.services.auth.base import AuthError, Principal

router = APIRouter()


@router.post(
    "/signup",
    response_model=SigninResponse,
    status_code=201,
    dependencies=[Depends(ip_limit("auth"))],
)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    provider = get_provider()
    try:
        user = await provider.register(
            db, email=payload.email, password=payload.password, name=payload.name
        )
        signed_in_user, token, expires_in = await provider.signin(
            db, email=payload.email, password=payload.password
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SigninResponse(
        user=UserResponse.model_validate(signed_in_user),
        token=TokenResponse(access_token=token, expires_in=expires_in),
    )


@router.post(
    "/signin",
    response_model=SigninResponse,
    dependencies=[Depends(ip_limit("auth"))],
)
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    provider = get_provider()
    # Per-account lockout only applies to local password auth — for delegated
    # providers (Logto) we never verify a password here, so failed attempts
    # aren't ours to count.
    track_failures = provider.name == "local"
    if track_failures:
        await assert_signin_allowed(payload.email)
    try:
        user, token, expires_in = await provider.signin(
            db, email=payload.email, password=payload.password
        )
    except AuthError as exc:
        if track_failures:
            await register_signin_failure(payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if track_failures:
        await clear_signin_failures(payload.email)
    return SigninResponse(
        user=UserResponse.model_validate(user),
        token=TokenResponse(access_token=token, expires_in=expires_in),
    )


@router.get("/me", response_model=UserResponse)
async def me(principal: Principal = Depends(require_user), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get_by_id(principal.user_id)
    if user is None:
        # Authenticated but the underlying user was deleted — treat as logged out.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user
