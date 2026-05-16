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
