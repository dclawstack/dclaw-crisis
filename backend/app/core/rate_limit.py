"""Fixed-window rate limit per principal, backed by Redis."""
from __future__ import annotations

import logging
import time

from fastapi import Depends, HTTPException, Request, status

from app.api.deps import require_user
from app.core.config import settings
from app.core.redis_client import get_redis
from app.services.auth.base import Principal

logger = logging.getLogger(__name__)


async def _check(bucket_key: str, limit: int, window_seconds: int) -> None:
    """Raise 429 if the principal has exceeded `limit` calls in the current window.

    Fixed-window counter (cheaper + simpler than sliding window; good enough
    for AI endpoint throttling). When Redis is unavailable the call is allowed.
    """
    client = get_redis()
    if client is None:
        return
    try:
        new_count = await client.incr(bucket_key)
        if new_count == 1:
            await client.expire(bucket_key, window_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate-limit check failed for %s: %s", bucket_key, exc)
        return  # fail open
    if new_count > limit:
        from app.core.metrics import rate_limit_blocks_total
        try:
            scope_label = bucket_key.split(":", 2)[1]
        except IndexError:
            scope_label = "unknown"
        rate_limit_blocks_total.labels(scope=scope_label).inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit} requests per {window_seconds}s",
            headers={"Retry-After": str(window_seconds)},
        )


def hourly_limit(scope: str, *, limit: int | None = None):
    """Build a FastAPI dependency that enforces an hourly rate limit per principal.

    Usage:
        @router.post("/...", dependencies=[Depends(hourly_limit("ai-summarize"))])
    """
    async def _dep(principal: Principal = Depends(require_user)) -> None:
        max_calls = limit if limit is not None else settings.ai_rate_limit_per_hour
        window = 3600
        now_hour = int(time.time() // window)
        bucket_key = f"rl:{scope}:{principal.user_id}:{now_hour}"
        await _check(bucket_key, max_calls, window)

    return _dep


def _client_ip(request: Request) -> str:
    """Best-effort client IP for per-IP throttling.

    Uses the socket peer (`request.client.host`). We deliberately do NOT trust
    X-Forwarded-For: without a configured trusted proxy it's attacker-spoofable,
    and honoring it would let a brute-forcer sidestep the limit by rotating the
    header. Behind a real proxy/LB, run uvicorn with --proxy-headers so
    `request.client` reflects the true peer.
    """
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def ip_limit(scope: str, *, limit: int | None = None, window_seconds: int = 60):
    """Build a FastAPI dependency that rate-limits per client IP.

    For pre-auth endpoints (e.g. /auth/signin) where there's no principal to
    key on. Usage:
        @router.post("/...", dependencies=[Depends(ip_limit("auth"))])
    """
    async def _dep(request: Request) -> None:
        max_calls = limit if limit is not None else settings.auth_rate_limit_per_minute
        now_window = int(time.time() // window_seconds)
        bucket_key = f"rl:{scope}-ip:{_client_ip(request)}:{now_window}"
        await _check(bucket_key, max_calls, window_seconds)

    return _dep


# ── Per-account sign-in lockout ──────────────────────────────────────────────
# Brute-forcing a single account from many IPs slips past ip_limit, so we also
# count *failed* sign-ins per account and lock it once they pile up. Tradeoff:
# an attacker who knows an email can lock that user out (a self-healing DoS) —
# the window is deliberately short to bound that, and a correct sign-in resets
# the counter immediately.

def _failed_signin_key(email: str) -> str:
    return f"auth-fail:{email.strip().lower()}"


async def assert_signin_allowed(email: str) -> None:
    """Raise 429 if `email` is locked out from repeated failed sign-ins.

    Fail-open when Redis is unavailable, mirroring `_check`.
    """
    client = get_redis()
    if client is None:
        return
    key = _failed_signin_key(email)
    try:
        raw = await client.get(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("signin-lock check failed for %s: %s", key, exc)
        return  # fail open
    if raw is not None and int(raw) >= settings.auth_max_failed_signins:
        try:
            ttl = int(await client.ttl(key))
        except Exception:  # noqa: BLE001
            ttl = settings.auth_lockout_seconds
        retry_after = ttl if ttl > 0 else settings.auth_lockout_seconds
        from app.core.metrics import rate_limit_blocks_total
        rate_limit_blocks_total.labels(scope="auth-lockout").inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to repeated failed sign-ins. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )


async def register_signin_failure(email: str) -> None:
    """Count a failed sign-in; the first failure starts the lockout window."""
    client = get_redis()
    if client is None:
        return
    key = _failed_signin_key(email)
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, settings.auth_lockout_seconds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("signin-fail record failed for %s: %s", key, exc)


async def clear_signin_failures(email: str) -> None:
    """Reset the failed-sign-in counter after a successful sign-in."""
    client = get_redis()
    if client is None:
        return
    try:
        await client.delete(_failed_signin_key(email))
    except Exception as exc:  # noqa: BLE001
        logger.warning("signin-fail clear failed: %s", exc)
