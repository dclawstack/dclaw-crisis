import pytest


@pytest.mark.asyncio
async def test_list_action_items(client):
    response = await client.get("/api/v1/action-items/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_action_item(client):
    # First create a crisis
    crisis_payload = {"title": "Test Crisis", "severity": "medium", "status": "detected", "category": "other"}
    crisis_resp = await client.post("/api/v1/crisis/", json=crisis_payload)
    crisis_id = crisis_resp.json()["id"]

    payload = {
        "crisis_id": crisis_id,
        "title": "Call supplier",
        "description": "Confirm outage details",
        "status": "pending",
        "priority": "high",
    }
    response = await client.post("/api/v1/action-items/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    item_id = data["id"]

    response = await client.get(f"/api/v1/action-items/{item_id}")
    assert response.status_code == 200
    assert response.json()["crisis_id"] == crisis_id


@pytest.mark.asyncio
async def test_update_action_item(client):
    crisis_payload = {"title": "Crisis", "severity": "low", "status": "detected", "category": "other"}
    crisis_resp = await client.post("/api/v1/crisis/", json=crisis_payload)
    crisis_id = crisis_resp.json()["id"]

    payload = {"crisis_id": crisis_id, "title": "Task", "status": "pending", "priority": "medium"}
    resp = await client.post("/api/v1/action-items/", json=payload)
    item_id = resp.json()["id"]

    update = {"status": "in_progress", "priority": "critical"}
    response = await client.put(f"/api/v1/action-items/{item_id}", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["priority"] == "critical"


@pytest.mark.asyncio
async def test_delete_action_item(client):
    crisis_payload = {"title": "Crisis", "severity": "low", "status": "detected", "category": "other"}
    crisis_resp = await client.post("/api/v1/crisis/", json=crisis_payload)
    crisis_id = crisis_resp.json()["id"]

    payload = {"crisis_id": crisis_id, "title": "Temp", "status": "pending", "priority": "low"}
    resp = await client.post("/api/v1/action-items/", json=payload)
    item_id = resp.json()["id"]

    response = await client.delete(f"/api/v1/action-items/{item_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/action-items/{item_id}")
    assert response.status_code == 404
