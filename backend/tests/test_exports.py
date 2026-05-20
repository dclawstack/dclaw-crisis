"""Tests for the MinIO-backed export endpoints (simulator mode)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_object_store():
    """Each test starts with a fresh in-memory bucket."""
    from app.core.object_store import InMemoryBackend, set_test_store
    InMemoryBackend._store = {}  # type: ignore[attr-defined]
    set_test_store(InMemoryBackend())
    yield
    set_test_store(None)


async def _crisis(client) -> str:
    res = await client.post(
        "/api/v1/crisis/",
        json={"title": "export test", "severity": "high", "status": "responding", "category": "security"},
    )
    return res.json()["id"]


# ── legal-hold export ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_export_legal_hold_uploads_and_returns_url(client):
    cid = await _crisis(client)
    hold = (await client.post(
        "/api/v1/legal-holds/",
        json={
            "crisis_id": cid,
            "title": "Q3 hold",
            "scope_description": "All payments data and email between 2026-01-01 and 2026-05-01",
            "custodians": [{"name": "Alice", "email": "[email protected]"}],
            "data_sources": ["M365 email", "payments db"],
            "hold_notice_text": "Preserve everything related to this matter.",
            "issued_by": "[email protected]",
        },
    )).json()

    res = await client.post(f"/api/v1/legal-holds/{hold['id']}/export")
    assert res.status_code == 200
    body = res.json()
    assert body["backend"] == "simulator"
    assert body["key"].startswith("legal-holds/")
    assert body["key"].endswith("/notice.txt")
    assert body["size_bytes"] > 0
    assert body["url"].startswith("/api/v1/exports/local/")

    # Download via the unprotected route (no auth header needed).
    download = await client.get(body["url"])
    assert download.status_code == 200
    text = download.text
    assert "LEGAL HOLD NOTICE" in text
    assert "Q3 hold" in text
    assert "Preserve everything related to this matter." in text


@pytest.mark.asyncio
async def test_export_legal_hold_404(client):
    res = await client.post("/api/v1/legal-holds/00000000-0000-0000-0000-000000000000/export")
    assert res.status_code == 404


# ── post-mortem export ─────────────────────────────────────────────────────


@pytest.fixture
def fake_post_mortem(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=1500):
        return {
            "timeline_summary": "Stuff happened. We responded. It ended.",
            "what_went_well": ["IC role spun up quickly", "Comms cadence held"],
            "what_went_poorly": ["Backups weren't tested in 60 days"],
            "root_cause": "Untested backup integrity allowed degraded recovery.",
            "lessons_learned": ["Quarterly backup test exercise", "Document recovery time"],
            "is_speculative": False,
        }
    from app.services import ai_post_mortem
    monkeypatch.setattr(ai_post_mortem, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_export_post_mortem_renders_markdown(client, fake_post_mortem):
    cid = await _crisis(client)
    res = await client.post(f"/api/v1/crisis/{cid}/export-post-mortem")
    assert res.status_code == 200
    body = res.json()
    assert body["key"].startswith("crises/")
    assert body["key"].endswith("/post-mortem.md")
    assert body["url"].startswith("/api/v1/exports/local/")

    download = await client.get(body["url"])
    assert download.status_code == 200
    md = download.text
    assert md.startswith("# Post-Mortem:")
    assert "## Timeline" in md
    assert "## Root cause" in md
    assert "## Lessons learned" in md
    assert "Untested backup integrity" in md
    # Confirm the markdown content type was set via file extension.
    assert "markdown" in download.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_export_post_mortem_404(client, fake_post_mortem):
    res = await client.post("/api/v1/crisis/00000000-0000-0000-0000-000000000000/export-post-mortem")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_local_export_download_404(client):
    res = await client.get("/api/v1/exports/local/nonexistent/path.txt")
    assert res.status_code == 404


# ── object_store backend selection ─────────────────────────────────────────


def test_object_store_falls_back_to_simulator_when_disabled():
    """With MINIO_DISABLED=true (conftest default) get_object_store returns the simulator."""
    from app.core import config as cfg
    from app.core.object_store import InMemoryBackend, get_object_store, set_test_store

    set_test_store(None)  # clear test injection so the real factory runs
    cfg.settings.minio_disabled = True
    store = get_object_store()
    assert isinstance(store, InMemoryBackend)
    assert store.backend == "simulator"


def test_object_store_returns_local_url():
    from app.core.object_store import InMemoryBackend

    store = InMemoryBackend()
    store.put_text("foo/bar.txt", "hello")
    url = store.presigned_get_url("foo/bar.txt")
    assert url == "/api/v1/exports/local/foo/bar.txt"
    assert store.get_text("foo/bar.txt") == "hello"
    assert store.exists("foo/bar.txt") is True
