"""Tests for the public /api/v1/demo/* seed + reset endpoints + ENABLE_DEMO_MODE gate."""
from __future__ import annotations

import pytest


@pytest.fixture
def demo_enabled(monkeypatch):
    """Flip ENABLE_DEMO_MODE on for the duration of a test."""
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "enable_demo_mode", True)


# ── Flag-off behavior (production default) ──────────────────────────────


@pytest.mark.asyncio
async def test_status_reports_disabled_when_flag_off(unauthenticated_client):
    res = await unauthenticated_client.get("/api/v1/demo/status")
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is False
    assert body["seeded"] is False
    assert all(v == 0 for v in body["counts"].values())


@pytest.mark.asyncio
async def test_seed_returns_403_when_flag_off(unauthenticated_client):
    res = await unauthenticated_client.post("/api/v1/demo/seed")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_reset_returns_403_when_flag_off(unauthenticated_client):
    res = await unauthenticated_client.delete("/api/v1/demo/reset")
    assert res.status_code == 403


# ── Endpoints are PUBLIC (no auth header required) ──────────────────────


@pytest.mark.asyncio
async def test_status_does_not_require_auth(unauthenticated_client, demo_enabled):
    res = await unauthenticated_client.get("/api/v1/demo/status")
    assert res.status_code == 200
    assert res.json()["enabled"] is True


@pytest.mark.asyncio
async def test_seed_does_not_require_auth(unauthenticated_client, demo_enabled):
    res = await unauthenticated_client.post("/api/v1/demo/seed")
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_reset_does_not_require_auth(unauthenticated_client, demo_enabled):
    await unauthenticated_client.post("/api/v1/demo/seed")
    res = await unauthenticated_client.delete("/api/v1/demo/reset")
    assert res.status_code == 200


# ── Seed creates dataset + demo user with credentials ───────────────────


@pytest.mark.asyncio
async def test_seed_creates_dataset_and_returns_credentials(unauthenticated_client, demo_enabled):
    res = await unauthenticated_client.post("/api/v1/demo/seed")
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is True
    assert body["seeded"] is True
    counts = body["counts"]
    assert counts["crises"] >= 2
    assert counts["stakeholders"] >= 5
    assert counts["signals"] >= 3

    creds = body["demo_credentials"]
    from app.core import config as cfg
    assert creds["email"] == cfg.settings.demo_user_email
    assert creds["password"] == cfg.settings.demo_user_password


@pytest.mark.asyncio
async def test_demo_user_can_sign_in_after_seed(unauthenticated_client, demo_enabled):
    seed_body = (await unauthenticated_client.post("/api/v1/demo/seed")).json()
    creds = seed_body["demo_credentials"]

    res = await unauthenticated_client.post("/api/v1/auth/signin", json=creds)
    assert res.status_code == 200
    assert res.json()["token"]["access_token"]
    assert res.json()["user"]["email"] == creds["email"]


@pytest.mark.asyncio
async def test_seed_is_idempotent(unauthenticated_client, demo_enabled):
    first = (await unauthenticated_client.post("/api/v1/demo/seed")).json()
    second = (await unauthenticated_client.post("/api/v1/demo/seed")).json()
    assert first["counts"]["crises"] == second["counts"]["crises"]
    assert second["result"]["skipped"] == "already-seeded"


# ── Reset removes demo data + demo user, leaves real data alone ─────────


@pytest.mark.asyncio
async def test_reset_removes_demo_data_and_user(unauthenticated_client, demo_enabled):
    await unauthenticated_client.post("/api/v1/demo/seed")

    pre = (await unauthenticated_client.get("/api/v1/demo/status")).json()
    assert pre["seeded"] is True

    reset = (await unauthenticated_client.delete("/api/v1/demo/reset")).json()
    assert reset["deleted"]["users"] == 1  # demo user gone
    assert reset["deleted"]["crises"] >= 2

    post = (await unauthenticated_client.get("/api/v1/demo/status")).json()
    assert post["seeded"] is False
    assert all(v == 0 for v in post["counts"].values())


@pytest.mark.asyncio
async def test_demo_user_cannot_sign_in_after_reset(unauthenticated_client, demo_enabled):
    seed_body = (await unauthenticated_client.post("/api/v1/demo/seed")).json()
    creds = seed_body["demo_credentials"]
    await unauthenticated_client.delete("/api/v1/demo/reset")
    res = await unauthenticated_client.post("/api/v1/auth/signin", json=creds)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_reset_leaves_real_data_alone(client, demo_enabled):
    """Real (non-DEMO-prefixed) data must survive a reset.

    Uses the authenticated `client` for operator-style writes — the
    /api/v1/demo/* endpoints don't need auth so they work with the same
    fixture (which has the require_user override installed but the demo
    router doesn't depend on it).
    """
    # Real crisis + team member created by an operator.
    real_crisis = (await client.post(
        "/api/v1/crisis/",
        json={"title": "Real outage — not demo", "severity": "high", "status": "responding", "category": "operational"},
    )).json()
    real_tm = (await client.post(
        "/api/v1/team-members/",
        json={"name": "Real Person", "email": "real-person-isolated@dclaw-crisis.example", "role": "On-call"},
    )).json()
    # A real signed-up user (not the demo user).
    real_user = (await client.post(
        "/api/v1/auth/signup",
        json={"email": "canary-real-user@dclaw-crisis.example", "password": "supersecret1"},
    )).json()
    real_user_id = real_user["user"]["id"]

    await client.post("/api/v1/demo/seed")
    await client.delete("/api/v1/demo/reset")

    # Real rows survived.
    assert (await client.get(f"/api/v1/crisis/{real_crisis['id']}")).status_code == 200
    assert (await client.get(f"/api/v1/team-members/{real_tm['id']}")).status_code == 200
    # Canary user still exists — sign-in works.
    signin = await client.post(
        "/api/v1/auth/signin",
        json={"email": "canary-real-user@dclaw-crisis.example", "password": "supersecret1"},
    )
    assert signin.status_code == 200
    assert signin.json()["user"]["id"] == real_user_id

    # No DEMO-prefixed crises remain.
    listing = (await client.get("/api/v1/crisis/")).json()
    assert all(not c["title"].startswith("DEMO: ") for c in listing)
