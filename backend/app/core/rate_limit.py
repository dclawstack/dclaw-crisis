"""Fixed-window rate limit per principal, backed by Redis."""
from __future__ import annotations

import logging
import time

from fastapi import Depends, HTTPException, status

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
