"""Idempotency-Key support for POST endpoints that accept retries.

External integrations (webhooks, RSS pollers) often retry on transient
failures. With `Idempotency-Key: <opaque-id>`, the first response is cached
in Redis under that key; subsequent identical requests get the same response
without re-executing the handler.

When Redis is disabled, idempotency becomes a no-op and the handler runs
every time — the contract is unchanged for callers that don't supply a key.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


def _key(scope: str, idem_key: str) -> str:
    return f"idem:{scope}:{idem_key}"


async def cached_or_run(
    scope: str,
    idem_key: str | None,
    *,
    ttl_seconds: int | None = None,
    producer: Callable[[], Awaitable[Any]],
) -> tuple[Any, bool]:
    """Return (response, replayed). If a cached response exists, returns (cached, True).

    Otherwise runs `producer`, caches its return value as JSON under the
    idempotency key, and returns (fresh, False). If `idem_key` is None or
    Redis is unavailable, runs and returns (fresh, False) without caching.
    """
    client = get_redis()
    if not idem_key or client is None:
        return await producer(), False

    full_key = _key(scope, idem_key)
    try:
        cached = await client.get(full_key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("idempotency lookup failed for %s: %s", full_key, exc)
        return await producer(), False

    if cached is not None:
        try:
            return json.loads(cached), True
        except (TypeError, ValueError):
            pass  # fall through and overwrite

    fresh = await producer()
    ttl = ttl_seconds if ttl_seconds is not None else settings.signals_idempotency_ttl_seconds
    try:
        await client.set(full_key, json.dumps(fresh, default=str), ex=ttl)
    except (TypeError, Exception) as exc:  # noqa: BLE001
        logger.warning("idempotency write failed for %s: %s", full_key, exc)
    return fresh, False
