import pytest


@pytest.mark.asyncio
async def test_list_playbooks(client):
    response = await client.get("/api/v1/playbooks/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_playbook(client):
    payload = {
        "name": "Supply Chain Outage Response",
        "category": "supply_chain",
        "description": "Standard playbook for supply chain disruptions.",
        "steps": [
            {"order": 1, "title": "Identify affected SKUs", "suggested_assignee_role": "Operations Lead"},
            {"order": 2, "title": "Contact alternate suppliers", "suggested_assignee_role": "Procurement"},
        ],
    }
    response = await client.post("/api/v1/playbooks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    pb_id = data["id"]

    response = await client.get(f"/api/v1/playbooks/{pb_id}")
    assert response.status_code == 200
    assert len(response.json()["steps"]) == 2


@pytest.mark.asyncio
async def test_update_playbook(client):
    payload = {"name": "Draft", "category": "other", "steps": []}
    resp = await client.post("/api/v1/playbooks/", json=payload)
    pb_id = resp.json()["id"]

    update = {"name": "Final Playbook", "steps": [{"order": 1, "title": "Step 1"}]}
    response = await client.put(f"/api/v1/playbooks/{pb_id}", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Final Playbook"
    assert len(data["steps"]) == 1


@pytest.mark.asyncio
async def test_delete_playbook(client):
    payload = {"name": "Temp", "category": "other", "steps": []}
    resp = await client.post("/api/v1/playbooks/", json=payload)
    pb_id = resp.json()["id"]

    response = await client.delete(f"/api/v1/playbooks/{pb_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/playbooks/{pb_id}")
    assert response.status_code == 404
