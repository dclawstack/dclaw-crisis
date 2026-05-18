"""Tests for signal ingestion + triage flow. LLM scorer is monkeypatched."""
from __future__ import annotations

import pytest

from app.services import ai_signal_scorer
from app.api.v1 import signals as signals_router


@pytest.fixture
def fake_scorer(monkeypatch):
    async def fake_score_signal(*, source, raw_text, source_url=None):
        # Drive the scoring path based on signal content so different tests can
        # exercise different scoring outcomes via input.
        text_lower = raw_text.lower()
        if "breach" in text_lower or "outage" in text_lower:
            return {
                "severity": "critical",
                "category": "security" if "breach" in text_lower else "operational",
                "confidence": 0.85,
                "summary": f"AI summary of: {raw_text[:80]}",
                "rationale": "High-impact keyword detected.",
                "is_crisis": True,
            }
        if "spam" in text_lower or "newsletter" in text_lower:
            return {
                "severity": "low",
                "category": "other",
                "confidence": 0.9,
                "summary": "Marketing noise.",
                "rationale": "Not a crisis.",
                "is_crisis": False,
            }
        return {
            "severity": "medium",
            "category": "operational",
            "confidence": 0.55,
            "summary": "Possible operational signal.",
            "rationale": "Ambiguous content.",
            "is_crisis": True,
        }

    monkeypatch.setattr(ai_signal_scorer, "score_signal", fake_score_signal)
    monkeypatch.setattr(signals_router, "score_signal", fake_score_signal)


@pytest.mark.asyncio
async def test_ingest_signal_auto_scores(client, fake_scorer):
    res = await client.post(
        "/api/v1/signals/",
        json={
            "source": "webhook:datadog",
            "raw_text": "Production database connection pool exhausted — major outage in progress.",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "new"
    assert data["ai_severity"] == "critical"
    assert data["ai_category"] == "operational"
    assert data["ai_confidence"] == 0.85
    assert data["ai_recommends_promotion"] is True
    assert data["ai_summary"].startswith("AI summary of:")


@pytest.mark.asyncio
async def test_ingest_noise_signal_does_not_recommend(client, fake_scorer):
    res = await client.post(
        "/api/v1/signals/",
        json={"source": "rss:marketing", "raw_text": "Our weekly newsletter is out!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["ai_severity"] == "low"
    assert data["ai_recommends_promotion"] is False


@pytest.mark.asyncio
async def test_ingest_without_auto_score(client, fake_scorer):
    res = await client.post(
        "/api/v1/signals/",
        json={
            "source": "manual",
            "raw_text": "Possible breach in payments service",
            "auto_score": False,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["ai_severity"] is None
    assert data["ai_recommends_promotion"] is False


@pytest.mark.asyncio
async def test_list_filter_by_status(client, fake_scorer):
    await client.post("/api/v1/signals/", json={"source": "x", "raw_text": "breach detected"})
    await client.post("/api/v1/signals/", json={"source": "y", "raw_text": "newsletter"})

    new_listing = await client.get("/api/v1/signals/?status=new")
    assert new_listing.status_code == 200
    assert len(new_listing.json()) == 2

    promoted = await client.get("/api/v1/signals/?status=promoted")
    assert promoted.json() == []


@pytest.mark.asyncio
async def test_rescore_signal(client, fake_scorer):
    created = (await client.post(
        "/api/v1/signals/",
        json={"source": "x", "raw_text": "Ambiguous report", "auto_score": False},
    )).json()
    assert created["ai_severity"] is None

    res = await client.post(f"/api/v1/signals/{created['id']}/rescore")
    assert res.status_code == 200
    assert res.json()["ai_severity"] == "medium"


@pytest.mark.asyncio
async def test_triage_signal(client, fake_scorer):
    s = (await client.post("/api/v1/signals/", json={"source": "x", "raw_text": "breach"})).json()
    res = await client.post(f"/api/v1/signals/{s['id']}/triage")
    assert res.status_code == 200
    assert res.json()["status"] == "triaged"


@pytest.mark.asyncio
async def test_dismiss_signal(client, fake_scorer):
    s = (await client.post("/api/v1/signals/", json={"source": "x", "raw_text": "newsletter"})).json()
    res = await client.post(f"/api/v1/signals/{s['id']}/dismiss")
    assert res.status_code == 200
    assert res.json()["status"] == "dismissed"


@pytest.mark.asyncio
async def test_promote_signal_creates_crisis(client, fake_scorer):
    s = (await client.post(
        "/api/v1/signals/",
        json={"source": "webhook:datadog", "raw_text": "Production database outage"},
    )).json()

    res = await client.post(f"/api/v1/signals/{s['id']}/promote", json={})
    assert res.status_code == 201
    promoted = res.json()
    assert promoted["status"] == "promoted"
    assert promoted["crisis_id"] is not None

    crisis = (await client.get(f"/api/v1/crisis/{promoted['crisis_id']}")).json()
    assert crisis["severity"] == "critical"
    assert crisis["category"] == "operational"
    assert crisis["status"] == "detected"
    assert "Production database outage" in crisis["description"]


@pytest.mark.asyncio
async def test_promote_with_overrides(client, fake_scorer):
    s = (await client.post(
        "/api/v1/signals/",
        json={"source": "manual", "raw_text": "Possible breach"},
    )).json()

    res = await client.post(
        f"/api/v1/signals/{s['id']}/promote",
        json={"title": "Custom Title", "description": "Operator note", "severity_override": "high"},
    )
    assert res.status_code == 201
    crisis_id = res.json()["crisis_id"]
    crisis = (await client.get(f"/api/v1/crisis/{crisis_id}")).json()
    assert crisis["title"] == "Custom Title"
    assert crisis["severity"] == "high"
    assert "Operator note" in crisis["description"]


@pytest.mark.asyncio
async def test_cannot_promote_twice(client, fake_scorer):
    s = (await client.post("/api/v1/signals/", json={"source": "x", "raw_text": "breach"})).json()
    first = await client.post(f"/api/v1/signals/{s['id']}/promote", json={})
    assert first.status_code == 201
    second = await client.post(f"/api/v1/signals/{s['id']}/promote", json={})
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_cannot_dismiss_promoted(client, fake_scorer):
    s = (await client.post("/api/v1/signals/", json={"source": "x", "raw_text": "breach"})).json()
    await client.post(f"/api/v1/signals/{s['id']}/promote", json={})
    res = await client.post(f"/api/v1/signals/{s['id']}/dismiss")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_404_paths(client, fake_scorer):
    bad = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/api/v1/signals/{bad}")).status_code == 404
    assert (await client.post(f"/api/v1/signals/{bad}/rescore")).status_code == 404
    assert (await client.post(f"/api/v1/signals/{bad}/dismiss")).status_code == 404
    assert (await client.post(f"/api/v1/signals/{bad}/triage")).status_code == 404
    assert (await client.post(f"/api/v1/signals/{bad}/promote", json={})).status_code == 404
