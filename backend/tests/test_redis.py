"""Tests for the Redis-backed cache / rate-limit / idempotency layers.

Each test that needs Redis pulls the `fake_redis` fixture which substitutes
fakeredis and flips `settings.redis_disabled = False`.
"""
from __future__ import annotations

import pytest


# ── cache.cache_get_or_set ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_get_or_set_calls_producer_once(fake_redis):
    from app.core.cache import cache_get_or_set
    calls = {"n": 0}

    async def producer():
        calls["n"] += 1
        return {"value": calls["n"]}

    first = await cache_get_or_set("test:key", 60, producer)
    second = await cache_get_or_set("test:key", 60, producer)
    assert first == {"value": 1}
    assert second == {"value": 1}
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_cache_disabled_skips_redis():
    """Without the fake_redis fixture, cache is no-op and producer always runs."""
    from app.core.cache import cache_get_or_set
    calls = {"n": 0}

    async def producer():
        calls["n"] += 1
        return calls["n"]

    a = await cache_get_or_set("x", 60, producer)
    b = await cache_get_or_set("x", 60, producer)
    assert a == 1
    assert b == 2  # not cached
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_cache_invalidate_prefix(fake_redis):
    from app.core.cache import cache_set, cache_invalidate_prefix, cache_get
    await cache_set("ai:summary:c1:v1", "first", 60)
    await cache_set("ai:summary:c2:v1", "second", 60)
    await cache_set("unrelated:key", "stays", 60)
    deleted = await cache_invalidate_prefix("ai:summary:")
    assert deleted == 2
    assert await cache_get("ai:summary:c1:v1") is None
    assert await cache_get("unrelated:key") == "stays"


# ── rate_limit.hourly_limit ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_threshold(fake_redis, client, monkeypatch):
    # Drop the limit way down so the test runs fast.
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "ai_rate_limit_per_hour", 2)

    # Use a cheap AI endpoint (summarize); patch the underlying generator so it
    # doesn't hit the LLM.
    from app.services import ai_summarizer

    async def fake_complete(system, user, *, temperature=0.3, max_tokens=800):
        class R: text = "ok"
        return R()
    monkeypatch.setattr(ai_summarizer, "complete", fake_complete)

    # Create a crisis to summarize.
    cid = (await client.post(
        "/api/v1/crisis/",
        json={"title": "rate-limit test", "severity": "low", "status": "detected", "category": "other"},
    )).json()["id"]

    r1 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    r2 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    r3 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
    assert r3.headers.get("Retry-After") == "3600"


@pytest.mark.asyncio
async def test_rate_limit_disabled_when_redis_off(client, monkeypatch):
    """Without Redis the limiter fails open — even tiny limits don't 429."""
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "ai_rate_limit_per_hour", 1)

    from app.services import ai_summarizer

    async def fake_complete(system, user, *, temperature=0.3, max_tokens=800):
        class R: text = "ok"
        return R()
    monkeypatch.setattr(ai_summarizer, "complete", fake_complete)

    cid = (await client.post(
        "/api/v1/crisis/",
        json={"title": "x", "severity": "low", "status": "detected", "category": "other"},
    )).json()["id"]
    r1 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    r2 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    assert r1.status_code == 200
    assert r2.status_code == 200  # would be 429 if Redis were enforcing


# ── idempotency on POST /signals/ ────────────────────────────────────────


@pytest.mark.asyncio
async def test_signal_idempotency_replays_response(fake_redis, client, monkeypatch):
    from app.services import ai_signal_scorer

    calls = {"n": 0}

    async def fake_score_signal(*, source, raw_text, source_url=None):
        calls["n"] += 1
        return {
            "severity": "high", "category": "security", "confidence": 0.9,
            "summary": "scored", "rationale": "test", "is_crisis": True,
        }
    monkeypatch.setattr(ai_signal_scorer, "score_signal", fake_score_signal)
    from app.api.v1 import signals as signals_router
    monkeypatch.setattr(signals_router, "score_signal", fake_score_signal)

    headers = {"Idempotency-Key": "client-uuid-123"}
    body = {"source": "webhook:test", "raw_text": "Possible breach in payments-api"}
    r1 = await client.post("/api/v1/signals/", json=body, headers=headers)
    r2 = await client.post("/api/v1/signals/", json=body, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    # Same body, same id — replayed not re-created
    assert r1.json()["id"] == r2.json()["id"]
    assert r2.headers.get("Idempotency-Replayed") == "true"
    # Scorer ran once
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_signal_without_idem_key_creates_each_time(fake_redis, client, monkeypatch):
    from app.services import ai_signal_scorer

    async def fake_score_signal(*, source, raw_text, source_url=None):
        return {
            "severity": "low", "category": "other", "confidence": 0.5,
            "summary": "low priority", "rationale": "test", "is_crisis": False,
        }
    monkeypatch.setattr(ai_signal_scorer, "score_signal", fake_score_signal)
    from app.api.v1 import signals as signals_router
    monkeypatch.setattr(signals_router, "score_signal", fake_score_signal)

    body = {"source": "manual", "raw_text": "duplicate"}
    r1 = await client.post("/api/v1/signals/", json=body)
    r2 = await client.post("/api/v1/signals/", json=body)
    assert r1.json()["id"] != r2.json()["id"]


# ── AI service caching via real flow ─────────────────────────────────────


@pytest.mark.asyncio
async def test_summarize_caches_per_crisis_version(fake_redis, client, monkeypatch):
    """Two summarize calls with no crisis change should hit the cache."""
    from app.services import ai_summarizer
    calls = {"n": 0}

    class FakeRes:
        def __init__(self, t): self.text = t

    async def fake_complete(system, user, *, temperature=0.3, max_tokens=800):
        calls["n"] += 1
        return FakeRes(f"summary {calls['n']}")
    monkeypatch.setattr(ai_summarizer, "complete", fake_complete)

    cid = (await client.post(
        "/api/v1/crisis/",
        json={"title": "cache test", "severity": "high", "status": "responding", "category": "operational"},
    )).json()["id"]

    r1 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    r2 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert calls["n"] == 1  # second call hit the cache


@pytest.mark.asyncio
async def test_summarize_cache_invalidated_when_crisis_updated(fake_redis, client, monkeypatch):
    """Updating the crisis bumps updated_at → cache key changes → LLM re-called."""
    from app.services import ai_summarizer

    class FakeRes:
        def __init__(self, t): self.text = t

    counter = {"n": 0}

    async def fake_complete(system, user, *, temperature=0.3, max_tokens=800):
        counter["n"] += 1
        return FakeRes(f"summary v{counter['n']}")
    monkeypatch.setattr(ai_summarizer, "complete", fake_complete)

    cid = (await client.post(
        "/api/v1/crisis/",
        json={"title": "v1", "severity": "high", "status": "responding", "category": "operational"},
    )).json()["id"]

    r1 = await client.post(f"/api/v1/crisis/{cid}/summarize")
    await client.put(f"/api/v1/crisis/{cid}", json={"title": "v2"})
    r2 = await client.post(f"/api/v1/crisis/{cid}/summarize")

    assert r1.json()["summary"] == "summary v1"
    assert r2.json()["summary"] == "summary v2"
    assert counter["n"] == 2
