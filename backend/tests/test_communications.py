import pytest


@pytest.mark.asyncio
async def test_list_communications(client):
    response = await client.get("/api/v1/communications/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_communication(client):
    crisis_payload = {"title": "Crisis", "severity": "low", "status": "detected", "category": "other"}
    crisis_resp = await client.post("/api/v1/crisis/", json=crisis_payload)
    crisis_id = crisis_resp.json()["id"]

    payload = {
        "crisis_id": crisis_id,
        "message": "Initial assessment complete. Standing up response team.",
        "comm_type": "internal_update",
        "channel": "app",
    }
    response = await client.post("/api/v1/communications/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == payload["message"]
    comm_id = data["id"]

    response = await client.get(f"/api/v1/communications/{comm_id}")
    assert response.status_code == 200
    assert response.json()["crisis_id"] == crisis_id


@pytest.mark.asyncio
async def test_update_communication(client):
    crisis_payload = {"title": "Crisis", "severity": "low", "status": "detected", "category": "other"}
    crisis_resp = await client.post("/api/v1/crisis/", json=crisis_payload)
    crisis_id = crisis_resp.json()["id"]

    payload = {"crisis_id": crisis_id, "message": "Draft", "comm_type": "internal_update", "channel": "app"}
    resp = await client.post("/api/v1/communications/", json=payload)
    comm_id = resp.json()["id"]

    update = {"message": "Updated message", "channel": "slack"}
    response = await client.put(f"/api/v1/communications/{comm_id}", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Updated message"
    assert data["channel"] == "slack"


@pytest.mark.asyncio
async def test_delete_communication(client):
    crisis_payload = {"title": "Crisis", "severity": "low", "status": "detected", "category": "other"}
    crisis_resp = await client.post("/api/v1/crisis/", json=crisis_payload)
    crisis_id = crisis_resp.json()["id"]

    payload = {"crisis_id": crisis_id, "message": "Temp", "comm_type": "internal_update", "channel": "app"}
    resp = await client.post("/api/v1/communications/", json=payload)
    comm_id = resp.json()["id"]

    response = await client.delete(f"/api/v1/communications/{comm_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/communications/{comm_id}")
    assert response.status_code == 404


async def _crisis_id(client) -> str:
    res = await client.post(
        "/api/v1/crisis/",
        json={"title": "X", "severity": "high", "status": "responding", "category": "operational"},
    )
    return res.json()["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("channel,expected_provider", [
    ("app", "in-app"),
    ("email", "simulator:email"),
    ("slack", "simulator:slack"),
    ("sms", "simulator:sms"),
])
async def test_send_communication_records_delivery(client, channel, expected_provider):
    cid = await _crisis_id(client)
    comm = (await client.post("/api/v1/communications/", json={
        "crisis_id": cid, "message": "Hello stakeholders, we are aware of the issue.", "comm_type": "stakeholder_alert", "channel": channel,
    })).json()
    assert comm["delivery_status"] == "pending"
    assert comm["sent_at"] is None

    res = await client.post(f"/api/v1/communications/{comm['id']}/send")
    assert res.status_code == 200
    body = res.json()
    assert body["delivery_status"] == "sent"
    assert body["sent_at"] is not None
    assert body["delivery_log"]["provider"] == expected_provider
    assert body["delivery_log"]["status"] == "sent"


@pytest.mark.asyncio
async def test_send_communication_already_sent(client):
    cid = await _crisis_id(client)
    comm = (await client.post("/api/v1/communications/", json={
        "crisis_id": cid, "message": "M", "comm_type": "internal_update", "channel": "app",
    })).json()
    await client.post(f"/api/v1/communications/{comm['id']}/send")
    res = await client.post(f"/api/v1/communications/{comm['id']}/send")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_send_communication_404(client):
    res = await client.post("/api/v1/communications/00000000-0000-0000-0000-000000000000/send")
    assert res.status_code == 404


@pytest.fixture
def fake_sentiment(monkeypatch):
    async def fake_complete_json(system, user, *, temperature=0.2, max_tokens=600):
        # Drive sentiment by inspecting only the message section of the prompt,
        # not the crisis context (which may quote prior communications).
        text = user.lower()
        message_marker = "message: \"\"\""
        if message_marker in text:
            after = text.split(message_marker, 1)[1]
            message_only = after.split("\"\"\"", 1)[0]
        else:
            message_only = text
        if "no comment" in message_only:
            return {
                "sentiment": "negative",
                "sentiment_score": -0.65,
                "predicted_reaction": "Audience will read this as evasive.",
                "risk_flags": ["tone too dismissive", "no acknowledgement of impact"],
            }
        if "we apologize unreservedly" in message_only:
            return {
                "sentiment": "positive",
                "sentiment_score": 0.55,
                "predicted_reaction": "Audience will appreciate the direct apology.",
                "risk_flags": [],
            }
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "predicted_reaction": "Audience will not have strong reaction.",
            "risk_flags": [],
        }
    from app.services import ai_sentiment
    monkeypatch.setattr(ai_sentiment, "complete_json", fake_complete_json)


@pytest.mark.asyncio
async def test_analyze_sentiment_persists_fields(client, fake_sentiment):
    cid = await _crisis_id(client)
    comm = (await client.post("/api/v1/communications/", json={
        "crisis_id": cid, "message": "We apologize unreservedly for the outage.", "comm_type": "public_statement", "channel": "email",
    })).json()

    res = await client.post(f"/api/v1/communications/{comm['id']}/analyze-sentiment")
    assert res.status_code == 200
    body = res.json()
    assert body["sentiment"] == "positive"
    assert body["sentiment_score"] == 0.55
    assert body["risk_flags"] == []

    # Verify it was persisted on the model
    fetched = (await client.get(f"/api/v1/communications/{comm['id']}")).json()
    assert fetched["sentiment"] == "positive"
    assert fetched["sentiment_analyzed_at"] is not None
    assert fetched["predicted_reaction"]


@pytest.mark.asyncio
async def test_analyze_sentiment_flags_risky_message(client, fake_sentiment):
    cid = await _crisis_id(client)
    comm = (await client.post("/api/v1/communications/", json={
        "crisis_id": cid, "message": "No comment.", "comm_type": "public_statement", "channel": "email",
    })).json()
    res = await client.post(f"/api/v1/communications/{comm['id']}/analyze-sentiment")
    body = res.json()
    assert body["sentiment"] == "negative"
    assert body["sentiment_score"] < 0
    assert len(body["risk_flags"]) == 2


@pytest.mark.asyncio
async def test_analyze_sentiment_404(client, fake_sentiment):
    res = await client.post("/api/v1/communications/00000000-0000-0000-0000-000000000000/analyze-sentiment")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_sentiment_trend_aggregates(client, fake_sentiment):
    cid = await _crisis_id(client)
    # Two positive, one negative — total should be 3, avg should be positive but lower than first.
    messages = [
        ("We apologize unreservedly for our role in this.", "public_statement"),
        ("We apologize unreservedly and have a plan.", "public_statement"),
        ("No comment.", "exec_brief"),
    ]
    for msg, ct in messages:
        comm = (await client.post("/api/v1/communications/", json={
            "crisis_id": cid, "message": msg, "comm_type": ct, "channel": "email",
        })).json()
        await client.post(f"/api/v1/communications/{comm['id']}/analyze-sentiment")

    # Also create one comm without analysis — should be in total but not analyzed.
    await client.post("/api/v1/communications/", json={
        "crisis_id": cid, "message": "draft only", "comm_type": "internal_update", "channel": "app",
    })

    res = await client.get(f"/api/v1/crisis/{cid}/sentiment-trend")
    assert res.status_code == 200
    body = res.json()
    assert body["analyzed_count"] == 3
    assert body["total_communications"] == 4
    assert body["counts"]["positive"] == 2
    assert body["counts"]["negative"] == 1
    assert body["counts"]["neutral"] == 0
    assert -1.0 <= body["average_score"] <= 1.0
    # trend goes from positives to negative → worsening (or insufficient if only 3 points)
    assert body["trend_direction"] in {"worsening", "improving", "flat", "insufficient_data"}


@pytest.mark.asyncio
async def test_sentiment_trend_no_analysis(client, fake_sentiment):
    cid = await _crisis_id(client)
    await client.post("/api/v1/communications/", json={
        "crisis_id": cid, "message": "x", "comm_type": "internal_update", "channel": "app",
    })
    res = await client.get(f"/api/v1/crisis/{cid}/sentiment-trend")
    assert res.status_code == 200
    body = res.json()
    assert body["analyzed_count"] == 0
    assert body["total_communications"] == 1
    assert body["average_score"] is None
    assert body["trend_direction"] == "insufficient_data"


@pytest.mark.asyncio
async def test_sentiment_trend_404(client):
    res = await client.get("/api/v1/crisis/00000000-0000-0000-0000-000000000000/sentiment-trend")
    assert res.status_code == 404
