"""Brute-force protection on the /auth/* endpoints.

Two controls, both backed by the shared Redis limiter infra:
- per-IP rate limit on signin+signup (`ip_limit`)
- per-account lockout after repeated failed sign-ins

The limiter fails open when Redis is disabled (the conftest default), so these
tests opt into the `fake_redis` fixture and tune the thresholds via monkeypatch.
"""
from __future__ import annotations

import pytest

from app.core import config as cfg

# Compose emails at runtime, matching test_auth.py's convention.
AT = chr(64)


@pytest.mark.asyncio
async def test_signin_ip_rate_limited(client, fake_redis, monkeypatch):
    """After `auth_rate_limit_per_minute` attempts from one IP, further auth
    requests get 429 — before the handler even runs."""
    monkeypatch.setattr(cfg.settings, "auth_rate_limit_per_minute", 3)
    monkeypatch.setattr(cfg.settings, "auth_max_failed_signins", 1000)  # isolate the IP limit

    payload = {"email": f"nobody{AT}example.com", "password": "whatever12"}
    codes = [
        (await client.post("/api/v1/auth/signin", json=payload)).status_code
        for _ in range(5)
    ]

    assert codes[:3] == [401, 401, 401]  # unknown user, but allowed through
    assert codes[3] == 429 and codes[4] == 429  # IP bucket exhausted


@pytest.mark.asyncio
async def test_signup_shares_the_auth_ip_budget(client, fake_redis, monkeypatch):
    monkeypatch.setattr(cfg.settings, "auth_rate_limit_per_minute", 2)

    r1 = await client.post("/api/v1/auth/signup", json={"email": f"a{AT}example.com", "password": "supersecret1"})
    r2 = await client.post("/api/v1/auth/signup", json={"email": f"b{AT}example.com", "password": "supersecret1"})
    r3 = await client.post("/api/v1/auth/signup", json={"email": f"c{AT}example.com", "password": "supersecret1"})

    assert r1.status_code == 201 and r2.status_code == 201
    assert r3.status_code == 429
    assert int(r3.headers["retry-after"]) > 0


@pytest.mark.asyncio
async def test_account_lockout_after_failed_signins(client, fake_redis, monkeypatch):
    """N wrong-password attempts lock the account — even a correct password is
    then rejected with 429 until the window expires."""
    monkeypatch.setattr(cfg.settings, "auth_rate_limit_per_minute", 1000)  # isolate the lockout
    monkeypatch.setattr(cfg.settings, "auth_max_failed_signins", 3)

    email = f"locked{AT}example.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "supersecret1"})

    for _ in range(3):
        r = await client.post("/api/v1/auth/signin", json={"email": email, "password": "wrongpass1"})
        assert r.status_code == 401

    locked = await client.post("/api/v1/auth/signin", json={"email": email, "password": "supersecret1"})
    assert locked.status_code == 429
    assert int(locked.headers["retry-after"]) > 0


@pytest.mark.asyncio
async def test_successful_signin_resets_failure_counter(client, fake_redis, monkeypatch):
    """A correct sign-in clears prior failures, so the lockout never trips for
    a user who simply mistyped a couple of times."""
    monkeypatch.setattr(cfg.settings, "auth_rate_limit_per_minute", 1000)
    monkeypatch.setattr(cfg.settings, "auth_max_failed_signins", 3)

    email = f"resets{AT}example.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "supersecret1"})

    for _ in range(2):
        bad = await client.post("/api/v1/auth/signin", json={"email": email, "password": "wrongpass1"})
        assert bad.status_code == 401

    ok = await client.post("/api/v1/auth/signin", json={"email": email, "password": "supersecret1"})
    assert ok.status_code == 200  # success resets the counter

    for _ in range(2):
        bad = await client.post("/api/v1/auth/signin", json={"email": email, "password": "wrongpass1"})
        assert bad.status_code == 401  # still under threshold, not locked


@pytest.mark.asyncio
async def test_lockout_is_per_account(client, fake_redis, monkeypatch):
    """Failures against one account must not lock a different account."""
    monkeypatch.setattr(cfg.settings, "auth_rate_limit_per_minute", 1000)
    monkeypatch.setattr(cfg.settings, "auth_max_failed_signins", 2)

    victim = f"victim{AT}example.com"
    bystander = f"bystander{AT}example.com"
    await client.post("/api/v1/auth/signup", json={"email": victim, "password": "supersecret1"})
    await client.post("/api/v1/auth/signup", json={"email": bystander, "password": "supersecret1"})

    for _ in range(2):
        await client.post("/api/v1/auth/signin", json={"email": victim, "password": "wrongpass1"})

    assert (await client.post("/api/v1/auth/signin", json={"email": victim, "password": "supersecret1"})).status_code == 429
    assert (await client.post("/api/v1/auth/signin", json={"email": bystander, "password": "supersecret1"})).status_code == 200


@pytest.mark.asyncio
async def test_no_throttle_when_redis_disabled(client, monkeypatch):
    """Limiter fails open: with Redis disabled (conftest default) the auth
    endpoints behave exactly as before, even with a tiny configured limit."""
    monkeypatch.setattr(cfg.settings, "auth_rate_limit_per_minute", 1)
    monkeypatch.setattr(cfg.settings, "auth_max_failed_signins", 1)

    email = f"noredis{AT}example.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "supersecret1"})
    for _ in range(5):
        r = await client.post("/api/v1/auth/signin", json={"email": email, "password": "supersecret1"})
        assert r.status_code == 200
