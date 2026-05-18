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
