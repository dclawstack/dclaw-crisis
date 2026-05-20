"""Tests for the auth provider, /auth/* endpoints, and the require_user dep."""
from __future__ import annotations

import pytest

# Compose emails at runtime to avoid editor auto-obfuscation of literal addresses.
AT = chr(64)
ALICE = f"alice{AT}example.com"
ALICE2 = f"alice2{AT}example.com"
BOB = f"bob{AT}example.com"
CAROL = f"carol{AT}example.com"
DAVE = f"dave{AT}example.com"
ERIN = f"erin{AT}example.com"
FRANK = f"frank{AT}example.com"
GINA = f"gina{AT}example.com"


# ─── Auth endpoints themselves ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_signup_returns_user_and_token(client):
    res = await client.post("/api/v1/auth/signup", json={
        "email": ALICE, "password": "supersecret1", "name": "Alice",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == ALICE
    assert body["user"]["auth_provider"] == "local"
    assert body["token"]["access_token"]
    assert body["token"]["token_type"] == "bearer"
    assert body["token"]["expires_in"] > 0


@pytest.mark.asyncio
async def test_signup_duplicate_email_400(client):
    payload = {"email": ALICE2, "password": "supersecret1"}
    assert (await client.post("/api/v1/auth/signup", json=payload)).status_code == 201
    res = await client.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 400
    assert "already" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_signin_with_correct_creds(client):
    await client.post("/api/v1/auth/signup", json={"email": BOB, "password": "supersecret1"})
    res = await client.post("/api/v1/auth/signin", json={"email": BOB, "password": "supersecret1"})
    assert res.status_code == 200
    assert res.json()["token"]["access_token"]


@pytest.mark.asyncio
async def test_signin_with_wrong_password_401(client):
    await client.post("/api/v1/auth/signup", json={"email": CAROL, "password": "supersecret1"})
    res = await client.post("/api/v1/auth/signin", json={"email": CAROL, "password": "wrongpass1"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_signin_unknown_user_401(client):
    res = await client.post("/api/v1/auth/signin", json={"email": f"ghost{AT}example.com", "password": "anything12"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_signup_short_password_validation(client):
    res = await client.post("/api/v1/auth/signup", json={"email": DAVE, "password": "short"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_signup_invalid_email_validation(client):
    res = await client.post("/api/v1/auth/signup", json={"email": "not-an-email", "password": "supersecret1"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_me_without_auth_returns_401_via_default_override(client):
    """With the conftest override the synthetic user_id has no DB row → 401."""
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_with_real_signup_returns_profile(client):
    """Sign up → use the returned token via the real require_user path."""
    signup = (await client.post("/api/v1/auth/signup", json={
        "email": ERIN, "password": "supersecret1", "name": "Erin",
    })).json()
    token = signup["token"]["access_token"]
    user_id = signup["user"]["id"]

    from app.api.main import app
    from app.api.deps.auth import require_user
    from tests.conftest import _override_require_user
    app.dependency_overrides.pop(require_user, None)
    try:
        res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["id"] == user_id
        assert res.json()["email"] == ERIN
    finally:
        app.dependency_overrides[require_user] = _override_require_user


# ─── require_user dependency (without the test override) ─────────────────────


@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(unauthenticated_client):
    res = await unauthenticated_client.get("/api/v1/crisis/")
    assert res.status_code == 401
    assert res.headers.get("www-authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_bad_token(unauthenticated_client):
    res = await unauthenticated_client.get(
        "/api/v1/crisis/", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_wrong_scheme(unauthenticated_client):
    res = await unauthenticated_client.get(
        "/api/v1/crisis/", headers={"Authorization": "Basic dGVzdA=="}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_accepts_valid_token(unauthenticated_client, client):
    signup = (await client.post("/api/v1/auth/signup", json={
        "email": FRANK, "password": "supersecret1",
    })).json()
    token = signup["token"]["access_token"]
    res = await unauthenticated_client.get(
        "/api/v1/crisis/", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_auth_endpoints_dont_require_token(unauthenticated_client):
    """Sign-up and sign-in must work without an existing token."""
    res = await unauthenticated_client.post("/api/v1/auth/signup", json={
        "email": GINA, "password": "supersecret1",
    })
    assert res.status_code == 201


@pytest.mark.asyncio
async def test_auth_disabled_short_circuits(unauthenticated_client, monkeypatch):
    """With AUTH_DISABLED=true, require_user returns the dev principal."""
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "auth_disabled", True)
    res = await unauthenticated_client.get("/api/v1/crisis/")
    assert res.status_code == 200


# ─── Sanity: existing test pattern still works under the default override ────


@pytest.mark.asyncio
async def test_existing_unauthenticated_call_works_via_override(client):
    """The default fixture overrides require_user — old tests don't need tokens."""
    res = await client.get("/api/v1/crisis/")
    assert res.status_code == 200
