"""Simple JSON cache built on Redis. No-op when Redis is disabled."""
from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable, TypeVar

from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def cache_get(key: str) -> Any | None:
    client = get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_get(%s) failed: %s", key, exc)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    client = get_redis()
    if client is None:
        return
    ttl = ttl_seconds if ttl_seconds is not None else settings.ai_cache_ttl_seconds
    try:
        await client.set(key, json.dumps(value), ex=ttl)
    except (TypeError, Exception) as exc:  # noqa: BLE001
        logger.warning("cache_set(%s) failed: %s", key, exc)


async def cache_get_or_set(
    key: str, ttl_seconds: int | None, producer: Callable[[], Awaitable[Any]]
) -> Any:
    """Return cached value at `key`, or compute via `producer` and cache it.

    Cache failures (or no Redis) fall through to the producer transparently.
    """
    cached = await cache_get(key)
    if cached is not None:
        return cached
    fresh = await producer()
    await cache_set(key, fresh, ttl_seconds)
    return fresh


async def cache_invalidate_prefix(prefix: str) -> int:
    """Delete all keys matching `<prefix>*`. Returns deleted count. No-op if no Redis."""
    client = get_redis()
    if client is None:
        return 0
    deleted = 0
    try:
        async for k in client.scan_iter(match=f"{prefix}*"):
            await client.delete(k)
            deleted += 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_invalidate_prefix(%s) failed: %s", prefix, exc)
    return deleted
