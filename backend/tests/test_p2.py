"""Tests for P2 features (simulation, continuity, media monitoring, legal hold)."""
from __future__ import annotations

import pytest


async def _make_crisis(client) -> str:
    res = await client.post(
        "/api/v1/crisis/",
        json={"title": "P2 test", "severity": "high", "status": "responding", "category": "security"},
    )
    return res.json()["id"]


# ── P2.1 Simulation ──────────────────────────────────────────────────────────


@pytest.fixture
def fake_scenario_gen(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.7, max_tokens=2000):
        return {
            "scenario": "A SQL injection on payments-api leaks 100K records starting 03:00 UTC.",
            "expected_actions": [
                {"order": 1, "action": "Contain the affected database", "role": "security_lead"},
                {"order": 2, "action": "Preserve forensic evidence", "role": "forensics"},
                {"order": 3, "action": "Notify legal counsel", "role": "general_counsel"},
            ],
            "expected_outcomes": ["Containment within 1 hour", "Legal notified within 2 hours"],
            "twist_at_minute_30": "Press inquiry from TechCrunch",
        }
    from app.services import ai_scenario_generator
    monkeypatch.setattr(ai_scenario_generator, "complete_json", fake_complete_json)


@pytest.fixture
def fake_sim_evaluator(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=1500):
        return {
            "summary": "Strong containment work, but legal notification was delayed.",
            "score": 0.72,
            "breakdown": [
                {"expected_outcome": "Containment within 1 hour", "achieved": "yes", "comment": "DB locked at T+45 min."},
                {"expected_outcome": "Legal notified within 2 hours", "achieved": "partial", "comment": "Notified at T+3h."},
            ],
        }
    from app.services import ai_simulation_evaluator
    monkeypatch.setattr(ai_simulation_evaluator, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_simulation_create_with_auto_generate(client, fake_scenario_gen):
    res = await client.post("/api/v1/simulations/", json={"name": "Q3 drill", "scenario_type": "security", "severity": "high"})
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "draft"
    assert "SQL injection" in body["generated_scenario"]
    assert len(body["generated_actions"]) == 3
    assert len(body["expected_outcomes"]) == 2


@pytest.mark.asyncio
async def test_simulation_full_flow(client, fake_scenario_gen, fake_sim_evaluator):
    sim = (await client.post("/api/v1/simulations/", json={"name": "Drill"})).json()
    started = (await client.post(f"/api/v1/simulations/{sim['id']}/start")).json()
    assert started["status"] == "running"
    assert started["started_at"] is not None

    # Cannot evaluate without operator_notes.
    res = await client.post(f"/api/v1/simulations/{sim['id']}/evaluate")
    assert res.status_code == 400

    await client.post(
        f"/api/v1/simulations/{sim['id']}/respond",
        json={"operator_notes": "Locked the DB at 45 min, paged GC at hour 3."},
    )

    eval_res = await client.post(f"/api/v1/simulations/{sim['id']}/evaluate")
    assert eval_res.status_code == 200
    body = eval_res.json()
    assert body["score"] == 0.72
    assert len(body["breakdown"]) == 2

    # Status should now be completed.
    final = (await client.get(f"/api/v1/simulations/{sim['id']}")).json()
    assert final["status"] == "completed"
    assert final["completed_at"] is not None


@pytest.mark.asyncio
async def test_simulation_cannot_start_twice(client, fake_scenario_gen):
    sim = (await client.post("/api/v1/simulations/", json={"name": "x"})).json()
    await client.post(f"/api/v1/simulations/{sim['id']}/start")
    res = await client.post(f"/api/v1/simulations/{sim['id']}/start")
    assert res.status_code == 400


# ── P2.2 Continuity Activation ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_activate_bcp_simulator_mode(client):
    """With CONTINUITY_API_URL unset, the simulator returns a stub activation."""
    cid = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{cid}/activate-bcp", json={"bcp_plan_name": "Security Incident BCP"})
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "activated"
    assert body["provider"] == "simulator"
    assert body["activated_at"] is not None
    assert body["response_payload"]["stub"] is True


@pytest.mark.asyncio
async def test_list_activations(client):
    cid = await _make_crisis(client)
    await client.post(f"/api/v1/crisis/{cid}/activate-bcp", json={"bcp_plan_name": "A"})
    await client.post(f"/api/v1/crisis/{cid}/activate-bcp", json={"bcp_plan_name": "B"})
    res = await client.get(f"/api/v1/crisis/{cid}/activations")
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.asyncio
async def test_activate_bcp_external_failure_recorded(client, monkeypatch):
    """If a configured external URL fails, the activation row records the failure."""
    cid = await _make_crisis(client)

    async def fake_activate_bcp(**kwargs):
        return {
            "provider": "dclaw-continuity",
            "status": "failed",
            "response_payload": {"request": kwargs},
            "error_message": "connection refused",
        }
    from app.api.v1 import crisis as crisis_router
    monkeypatch.setattr(crisis_router, "activate_bcp", fake_activate_bcp)

    res = await client.post(f"/api/v1/crisis/{cid}/activate-bcp", json={})
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "failed"
    assert body["error_message"] == "connection refused"
    assert body["activated_at"] is None


# ── P2.3 Media Monitoring ────────────────────────────────────────────────────


@pytest.fixture
def fake_media_sentiment(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=500):
        text = user.lower()
        if "scandal" in text or "investigation" in text:
            return {
                "sentiment": "negative",
                "sentiment_score": -0.6,
                "key_themes": ["regulatory pressure", "trust erosion", "executive accountability"],
            }
        if "praised" in text or "industry-leading" in text:
            return {
                "sentiment": "positive",
                "sentiment_score": 0.7,
                "key_themes": ["transparent response", "rapid mitigation"],
            }
        return {"sentiment": "neutral", "sentiment_score": 0.0, "key_themes": ["factual report"]}
    from app.services import ai_media_sentiment
    monkeypatch.setattr(ai_media_sentiment, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_media_ingest_auto_analyzes(client, fake_media_sentiment):
    cid = await _make_crisis(client)
    res = await client.post(
        "/api/v1/media-mentions/",
        json={
            "outlet": "TechCrunch",
            "headline": "Company faces investigation over data practices",
            "snippet": "Sources say the SEC has opened an investigation into the company's disclosure practices.",
            "crisis_id": cid,
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["sentiment"] == "negative"
    assert body["sentiment_score"] < 0
    assert body["analyzed_at"] is not None


@pytest.mark.asyncio
async def test_media_coverage_aggregates(client, fake_media_sentiment):
    cid = await _make_crisis(client)
    snippets = [
        ("TechCrunch", "investigation into our disclosure practices"),
        ("Reuters", "Company praised by analysts for industry-leading response"),
        ("AP", "A factual brief report on the incident."),
    ]
    for outlet, snip in snippets:
        await client.post(
            "/api/v1/media-mentions/",
            json={"outlet": outlet, "snippet": snip, "crisis_id": cid},
        )

    res = await client.get(f"/api/v1/media-mentions/coverage/{cid}")
    assert res.status_code == 200
    body = res.json()
    assert body["total_mentions"] == 3
    assert body["analyzed_count"] == 3
    assert body["counts"]["negative"] == 1
    assert body["counts"]["positive"] == 1
    assert body["counts"]["neutral"] == 1
    assert body["by_outlet"]["TechCrunch"] == 1
    assert len(body["top_themes"]) >= 1


@pytest.mark.asyncio
async def test_media_no_auto_analyze(client, fake_media_sentiment):
    res = await client.post(
        "/api/v1/media-mentions/",
        json={"outlet": "X", "snippet": "any", "auto_analyze": False},
    )
    assert res.status_code == 201
    assert res.json()["sentiment"] is None


# ── P2.4 Legal Hold ──────────────────────────────────────────────────────────


@pytest.fixture
def fake_legal_drafter(monkeypatch):
    from app.services import ai_legal_hold

    class FakeResp:
        def __init__(self, text):
            self.text = text

    async def fake_complete(system, user, *, temperature=0.3, max_tokens=900):
        return FakeResp(
            "[AI-GENERATED DRAFT — NOT LEGAL ADVICE. Have outside counsel review before issuing.]\n\n"
            "MATTER: Q3 Security Incident\n\nAll employees must preserve relevant documents..."
        )

    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=1200):
        return {
            "data_sources": [
                {"name": "Email archive (M365)", "type": "email", "rationale": "Communications about the incident"},
                {"name": "Postgres prod (payments)", "type": "database", "rationale": "Affected data store"},
            ],
            "custodians": [
                {"role": "CISO", "reason": "Security incident response owner"},
                {"role": "General Counsel", "reason": "Privilege over legal communications"},
            ],
            "preservation_duration_days_min": 365,
        }

    monkeypatch.setattr(ai_legal_hold, "complete", fake_complete)
    monkeypatch.setattr(ai_legal_hold, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_legal_hold_full_lifecycle(client):
    cid = await _make_crisis(client)
    # Create draft
    hold = (await client.post(
        "/api/v1/legal-holds/",
        json={"crisis_id": cid, "title": "Q3 hold", "scope_description": "All payments data", "custodians": [{"name": "Alice", "email": "a@x.com"}], "data_sources": ["email", "db"]},
    )).json()
    assert hold["status"] == "draft"

    # Cannot issue without hold_notice_text
    res = await client.post(f"/api/v1/legal-holds/{hold['id']}/issue")
    assert res.status_code == 400

    await client.put(f"/api/v1/legal-holds/{hold['id']}", json={"hold_notice_text": "Preserve everything related to this matter."})
    issued = (await client.post(f"/api/v1/legal-holds/{hold['id']}/issue")).json()
    assert issued["status"] == "active"
    assert issued["issued_at"] is not None

    # Cannot modify while active
    res = await client.put(f"/api/v1/legal-holds/{hold['id']}", json={"title": "new"})
    assert res.status_code == 400

    # Cannot delete while active
    res = await client.delete(f"/api/v1/legal-holds/{hold['id']}")
    assert res.status_code == 400

    released = (await client.post(f"/api/v1/legal-holds/{hold['id']}/release", json={"reason": "Matter resolved."})).json()
    assert released["status"] == "released"
    assert released["released_at"] is not None

    # Can delete now
    res = await client.delete(f"/api/v1/legal-holds/{hold['id']}")
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_draft_hold_notice_endpoint(client, fake_legal_drafter):
    cid = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{cid}/draft-hold-notice")
    assert res.status_code == 200
    body = res.json()
    assert "[AI-GENERATED DRAFT" in body["notice_text"]
    assert "NOT LEGAL ADVICE" in body["notice_text"]


@pytest.mark.asyncio
async def test_recommend_evidence_endpoint(client, fake_legal_drafter):
    cid = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{cid}/recommend-evidence")
    assert res.status_code == 200
    body = res.json()
    assert len(body["data_sources"]) == 2
    assert body["data_sources"][0]["type"] in {"email", "chat", "document_repo", "database", "logs", "backups", "other"}
    assert body["preservation_duration_days_min"] == 365


@pytest.mark.asyncio
async def test_list_legal_holds_filters(client):
    cid = await _make_crisis(client)
    await client.post("/api/v1/legal-holds/", json={"crisis_id": cid, "title": "h1"})
    await client.post("/api/v1/legal-holds/", json={"crisis_id": cid, "title": "h2"})

    by_crisis = (await client.get(f"/api/v1/legal-holds/?crisis_id={cid}")).json()
    assert len(by_crisis) == 2

    active_only = (await client.get("/api/v1/legal-holds/?active_only=true")).json()
    assert len(active_only) == 0  # all are draft


@pytest.mark.asyncio
async def test_404_paths(client):
    bad = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/api/v1/simulations/{bad}")).status_code == 404
    assert (await client.post(f"/api/v1/simulations/{bad}/start")).status_code == 404
    assert (await client.get(f"/api/v1/media-mentions/{bad}")).status_code == 404
    assert (await client.get(f"/api/v1/legal-holds/{bad}")).status_code == 404
    assert (await client.post(f"/api/v1/crisis/{bad}/activate-bcp", json={})).status_code == 404
    assert (await client.post(f"/api/v1/crisis/{bad}/draft-hold-notice")).status_code == 404
    assert (await client.post(f"/api/v1/crisis/{bad}/recommend-evidence")).status_code == 404
