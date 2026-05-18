"""Tests for AI endpoints. LLM calls are monkeypatched — no network access required."""
from __future__ import annotations

import pytest

from app.services import llm as llm_module
from app.services.llm import LLMResponse


@pytest.fixture
def fake_llm(monkeypatch):
    async def fake_chat(messages, *, temperature=0.4, max_tokens=1024):
        last = messages[-1]
        last_content = last["content"] if isinstance(last, dict) else last.content
        return LLMResponse(text=f"FAKE: {last_content[:80]}", provider="fake", model="fake-1")

    async def fake_complete(system, user, *, temperature=0.4, max_tokens=1024):
        return LLMResponse(text=f"FAKE SUMMARY for: {user[:60]}", provider="fake", model="fake-1")

    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=1024):
        return {
            "title": "Notify legal counsel",
            "description": "Schedule a brief with outside counsel within 4 hours.",
            "priority": "high",
            "rationale": "Legal exposure is unmitigated.",
            "suggested_assignee_role": "general_counsel",
        }

    monkeypatch.setattr(llm_module, "chat", fake_chat)
    monkeypatch.setattr(llm_module, "complete", fake_complete)
    monkeypatch.setattr(llm_module, "complete_json", fake_complete_json)
    # Patch already-imported references in the AI service modules
    from app.services import ai_summarizer, ai_recommender, ai_comm_draft, copilot
    monkeypatch.setattr(ai_summarizer, "complete", fake_complete)
    monkeypatch.setattr(ai_recommender, "complete_json", fake_complete_json)
    monkeypatch.setattr(ai_comm_draft, "complete", fake_complete)
    monkeypatch.setattr(copilot, "chat", fake_chat)


async def _make_crisis(client) -> str:
    payload = {
        "title": "Data breach detected",
        "description": "Suspected SQL injection on payments service",
        "severity": "critical",
        "status": "responding",
        "category": "security",
    }
    res = await client.post("/api/v1/crisis/", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_summarize_crisis(client, fake_llm):
    crisis_id = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{crisis_id}/summarize")
    assert res.status_code == 200
    body = res.json()
    assert "summary" in body
    assert body["summary"].startswith("FAKE SUMMARY")


@pytest.mark.asyncio
async def test_summarize_404(client, fake_llm):
    res = await client.post("/api/v1/crisis/00000000-0000-0000-0000-000000000000/summarize")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_next_action(client, fake_llm):
    crisis_id = await _make_crisis(client)
    res = await client.get(f"/api/v1/crisis/{crisis_id}/next-action")
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Notify legal counsel"
    assert body["priority"] == "high"
    assert body["suggested_assignee_role"] == "general_counsel"


@pytest.mark.asyncio
async def test_draft_communication(client, fake_llm):
    crisis_id = await _make_crisis(client)
    res = await client.post(
        "/api/v1/communications/draft",
        json={
            "crisis_id": crisis_id,
            "comm_type": "stakeholder_alert",
            "channel": "email",
            "audience": "Enterprise customers",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["comm_type"] == "stakeholder_alert"
    assert body["channel"] == "email"
    assert body["draft"].startswith("FAKE SUMMARY")


@pytest.mark.asyncio
async def test_draft_communication_404(client, fake_llm):
    res = await client.post(
        "/api/v1/communications/draft",
        json={"crisis_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_copilot_chat(client, fake_llm):
    await _make_crisis(client)
    res = await client.post(
        "/api/v1/copilot/chat",
        json={"messages": [{"role": "user", "content": "What's our top priority right now?"}]},
    )
    assert res.status_code == 200
    body = res.json()
    assert "reply" in body
    assert body["reply"].startswith("FAKE:")


@pytest.mark.asyncio
async def test_copilot_empty_messages(client, fake_llm):
    res = await client.post("/api/v1/copilot/chat", json={"messages": []})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_copilot_focused_crisis(client, fake_llm):
    crisis_id = await _make_crisis(client)
    res = await client.post(
        "/api/v1/copilot/chat",
        json={
            "focused_crisis_id": crisis_id,
            "messages": [{"role": "user", "content": "Summarize this incident."}],
        },
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_llm_unavailable_returns_503(client, monkeypatch):
    """If no provider is reachable, endpoints should return 503."""
    from app.services import ai_summarizer
    from app.services.llm import LLMUnavailableError

    async def boom(*args, **kwargs):
        raise LLMUnavailableError("no provider")

    monkeypatch.setattr(ai_summarizer, "complete", boom)

    crisis_id = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{crisis_id}/summarize")
    assert res.status_code == 503


@pytest.fixture
def fake_post_mortem(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=1024):
        return {
            "timeline_summary": "Detected at 14:00, escalated by 14:15, mitigation at 14:45.",
            "what_went_well": ["IC role activated within 3 minutes", "Customer comms went out on time"],
            "what_went_poorly": ["Initial severity was under-scored", "Runbook step 4 was wrong"],
            "root_cause": "Misconfigured webhook retry policy under spike load.",
            "lessons_learned": ["Add circuit-breaker to webhook handler", "Update runbook step 4"],
            "is_speculative": False,
        }

    from app.services import ai_post_mortem
    monkeypatch.setattr(ai_post_mortem, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_post_mortem_endpoint(client, fake_post_mortem):
    crisis_id = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{crisis_id}/post-mortem")
    assert res.status_code == 200
    body = res.json()
    assert "Detected at 14:00" in body["timeline_summary"]
    assert len(body["what_went_well"]) == 2
    assert len(body["lessons_learned"]) == 2
    assert body["is_speculative"] is False


@pytest.mark.asyncio
async def test_post_mortem_404(client, fake_post_mortem):
    res = await client.post("/api/v1/crisis/00000000-0000-0000-0000-000000000000/post-mortem")
    assert res.status_code == 404


@pytest.fixture
def fake_playbook_advisor(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=1500):
        return {
            "summary": "Two refinements based on incident response gaps.",
            "suggested_changes": [
                {
                    "kind": "add_step",
                    "step_order": None,
                    "new_title": "Auto-disable webhook retries during incident",
                    "new_description": "Add a circuit breaker step before mitigation.",
                    "new_role": "on_call_engineer",
                    "rationale": "Saturation of retries amplified the outage.",
                },
                {
                    "kind": "rewrite_step",
                    "step_order": 4,
                    "new_title": "Validate dependent service health before declaring containment",
                    "new_description": None,
                    "new_role": None,
                    "rationale": "Previously skipped downstream verification.",
                },
                # Junk entries below should be filtered out.
                {"kind": "invalid_kind", "rationale": "nope"},
                "not a dict",
            ],
        }

    from app.services import ai_playbook_advisor
    monkeypatch.setattr(ai_playbook_advisor, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_playbook_advisor_endpoint_with_matching_category(client, fake_playbook_advisor):
    # Seed at least one playbook in the same category as our crisis (security).
    pb_payload = {
        "name": "Test Sec Plan",
        "category": "security",
        "description": "test",
        "steps": [{"order": 1, "title": "step a"}, {"order": 2, "title": "step b"}],
    }
    await client.post("/api/v1/playbooks/", json=pb_payload)

    crisis_id = await _make_crisis(client)
    res = await client.post(f"/api/v1/crisis/{crisis_id}/suggest-playbook-updates")
    assert res.status_code == 200
    body = res.json()
    assert body["playbook_name"] == "Test Sec Plan"
    # Junk entries filtered out: should be 2 valid changes.
    assert len(body["suggested_changes"]) == 2
    kinds = [c["kind"] for c in body["suggested_changes"]]
    assert "add_step" in kinds
    assert "rewrite_step" in kinds


@pytest.mark.asyncio
async def test_playbook_advisor_no_matching_playbook(client, fake_playbook_advisor):
    crisis_id = await _make_crisis(client)  # security category, no security playbooks exist
    res = await client.post(f"/api/v1/crisis/{crisis_id}/suggest-playbook-updates")
    assert res.status_code == 200
    body = res.json()
    assert body["playbook_id"] is None
    assert "No existing playbook" in body["summary"]
    assert body["suggested_changes"] == []


@pytest.fixture
def fake_playbook_customizer(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.3, max_tokens=2000):
        # Echo back rewritten steps preserving order.
        return {
            "steps": [
                {"order": 1, "title": "AI: Step one tailored", "description": "Specific to incident.", "suggested_assignee_role": "ignored_in_output"},
                {"order": 2, "title": "AI: Step two tailored", "description": "Also specific.", "suggested_assignee_role": "ignored_in_output"},
            ],
        }

    from app.services import ai_playbook_customizer
    monkeypatch.setattr(ai_playbook_customizer, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_instantiate_with_ai_customization(client, fake_playbook_customizer):
    pb_payload = {
        "name": "Cust Plan",
        "category": "operational",
        "description": "generic plan",
        "steps": [
            {"order": 1, "title": "Generic step one", "suggested_assignee_role": "role_a"},
            {"order": 2, "title": "Generic step two", "suggested_assignee_role": "role_b"},
        ],
    }
    pb = (await client.post("/api/v1/playbooks/", json=pb_payload)).json()

    res = await client.post(
        f"/api/v1/playbooks/{pb['id']}/instantiate",
        json={
            "title": "Live incident",
            "severity": "high",
            "incident_context": "Stripe webhooks failing in payments service since 14:00 UTC.",
            "ai_customize": True,
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["ai_customized"] is True
    crisis_id = body["crisis"]["id"]

    actions = (await client.get(f"/api/v1/action-items/?crisis_id={crisis_id}")).json()
    titles = sorted([a["title"] for a in actions])
    assert titles == ["AI: Step one tailored", "AI: Step two tailored"]


@pytest.mark.asyncio
async def test_instantiate_ai_customize_without_context_falls_back(client, fake_playbook_customizer):
    pb_payload = {
        "name": "Cust Plan 2",
        "category": "operational",
        "steps": [{"order": 1, "title": "Generic only"}],
    }
    pb = (await client.post("/api/v1/playbooks/", json=pb_payload)).json()

    # ai_customize=True but no context — should fall back to generic, not call the AI.
    res = await client.post(
        f"/api/v1/playbooks/{pb['id']}/instantiate",
        json={"title": "x", "severity": "low", "ai_customize": True},
    )
    assert res.status_code == 201
    assert res.json()["ai_customized"] is False
    crisis_id = res.json()["crisis"]["id"]
    actions = (await client.get(f"/api/v1/action-items/?crisis_id={crisis_id}")).json()
    assert actions[0]["title"] == "Generic only"
