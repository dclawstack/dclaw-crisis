"""Tests for the /api/v1/demo/* seed + clear endpoints."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_status_when_empty(client):
    res = await client.get("/api/v1/demo/status")
    assert res.status_code == 200
    body = res.json()
    assert body["seeded"] is False
    assert all(v == 0 for v in body["counts"].values())


@pytest.mark.asyncio
async def test_seed_creates_realistic_dataset(client):
    res = await client.post("/api/v1/demo/seed")
    assert res.status_code == 200
    body = res.json()
    assert body["crises"] >= 2
    assert body["team_members"] >= 3
    assert body["stakeholders"] >= 5
    assert body["resources"] >= 6
    assert body["signals"] >= 3
    assert body["simulations"] >= 1
    assert body["legal_holds"] >= 1
    assert body["media_mentions"] >= 2

    # Status now reports seeded.
    status = (await client.get("/api/v1/demo/status")).json()
    assert status["seeded"] is True


@pytest.mark.asyncio
async def test_seed_is_idempotent(client):
    first = (await client.post("/api/v1/demo/seed")).json()
    second = (await client.post("/api/v1/demo/seed")).json()
    assert first["crises"] == second["crises"]
    assert second["skipped"] == "already-seeded"


@pytest.mark.asyncio
async def test_clear_removes_demo_data(client):
    await client.post("/api/v1/demo/seed")
    pre_status = (await client.get("/api/v1/demo/status")).json()
    assert pre_status["seeded"] is True

    res = await client.post("/api/v1/demo/clear")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] > 0

    post_status = (await client.get("/api/v1/demo/status")).json()
    assert post_status["seeded"] is False


@pytest.mark.asyncio
async def test_clear_leaves_real_data_alone(client):
    # Real crisis + team member created by the operator.
    real_crisis = (await client.post(
        "/api/v1/crisis/",
        json={"title": "Real outage — not demo", "severity": "high", "status": "responding", "category": "operational"},
    )).json()
    real_tm = (await client.post(
        "/api/v1/team-members/",
        json={"name": "Real Person", "email": "real-person@dclaw-crisis.example", "role": "On-call"},
    )).json()

    await client.post("/api/v1/demo/seed")
    await client.post("/api/v1/demo/clear")

    # Real rows survived.
    assert (await client.get(f"/api/v1/crisis/{real_crisis['id']}")).status_code == 200
    assert (await client.get(f"/api/v1/team-members/{real_tm['id']}")).status_code == 200

    # All demo rows gone.
    listing = (await client.get("/api/v1/crisis/")).json()
    assert all(not c["title"].startswith("DEMO: ") for c in listing)


@pytest.mark.asyncio
async def test_demo_endpoints_require_auth(unauthenticated_client):
    assert (await unauthenticated_client.get("/api/v1/demo/status")).status_code == 401
    assert (await unauthenticated_client.post("/api/v1/demo/seed")).status_code == 401
    assert (await unauthenticated_client.post("/api/v1/demo/clear")).status_code == 401
