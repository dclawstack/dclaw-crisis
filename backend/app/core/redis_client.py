"""Redis client singleton + helpers.

Three uses for PRD §4 Redis:
- AI response caching (`core/cache.py`)
- Per-principal rate limiting on AI endpoints (`core/rate_limit.py`)
- Idempotency keys on signal ingestion (`core/idempotency.py`)

When `REDIS_DISABLED=true` (or the import of `redis.asyncio` fails), the
client is `None` and the higher-level helpers degrade gracefully —
`cache_get_or_set` calls the underlying function, rate limit allows, and
idempotency keys are not checked. Tests run with redis_disabled=True by
default; specific Redis behaviors are exercised against fakeredis.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

try:  # Optional dependency at import time so tests work without redis-py installed in some envs.
    from redis import asyncio as aioredis  # type: ignore
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]

_client: Any | None = None
_override_client: Any | None = None


def set_test_client(client: Any | None) -> None:
    """Inject a fakeredis (or any aioredis-compatible) client for tests."""
    global _override_client
    _override_client = client


def get_redis() -> Any | None:
    """Return the async redis client, or None when disabled / unavailable."""
    if _override_client is not None:
        return _override_client
    if settings.redis_disabled or aioredis is None:
        return None
    global _client
    if _client is None:
        try:
            _client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis init failed: %s — falling back to disabled mode", exc)
            _client = None
    return _client


async def ping() -> bool:
    client = get_redis()
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis ping failed: %s", exc)
        return False
