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


@pytest.mark.asyncio
async def test_seed_playbooks_is_idempotent(client):
    r1 = await client.post("/api/v1/playbooks/seed")
    assert r1.status_code == 200
    assert r1.json()["created"] >= 5

    r2 = await client.post("/api/v1/playbooks/seed")
    assert r2.status_code == 200
    assert r2.json()["created"] == 0
    assert r2.json()["skipped"] >= 5

    listing = await client.get("/api/v1/playbooks/")
    names = {p["name"] for p in listing.json()}
    assert "Data Breach Response" in names
    assert "Production Outage" in names


@pytest.mark.asyncio
async def test_instantiate_playbook_creates_crisis_with_actions(client):
    pb_payload = {
        "name": "Test Plan",
        "category": "security",
        "description": "Test description",
        "steps": [
            {"order": 1, "title": "Step one", "description": "Do this first"},
            {"order": 2, "title": "Step two"},
            {"order": 3, "title": "Step three"},
        ],
    }
    pb = (await client.post("/api/v1/playbooks/", json=pb_payload)).json()

    res = await client.post(
        f"/api/v1/playbooks/{pb['id']}/instantiate",
        json={"title": "Q3 Intrusion", "severity": "high"},
    )
    assert res.status_code == 201
    crisis = res.json()
    assert crisis["title"] == "Q3 Intrusion"
    assert crisis["category"] == "security"
    assert crisis["status"] == "responding"

    actions = (await client.get(f"/api/v1/action-items/?crisis_id={crisis['id']}")).json()
    assert len(actions) == 3
    titles = [a["title"] for a in actions]
    assert "Step one" in titles


@pytest.mark.asyncio
async def test_instantiate_playbook_404(client):
    res = await client.post(
        "/api/v1/playbooks/00000000-0000-0000-0000-000000000000/instantiate",
        json={"title": "anything"},
    )
    assert res.status_code == 404
