import pytest
from httpx import AsyncClient, ASGITransport

from app.api.main import app


@pytest.mark.asyncio
async def test_list_crises(client):
    response = await client.get("/api/v1/crisis/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_crisis(client):
    payload = {
        "title": "Supply Chain Disruption",
        "description": "Critical supplier outage",
        "severity": "critical",
        "status": "detected",
        "category": "supply_chain",
        "estimated_impact_usd": 500000.0,
    }
    response = await client.post("/api/v1/crisis/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    crisis_id = data["id"]

    response = await client.get(f"/api/v1/crisis/{crisis_id}")
    assert response.status_code == 200
    assert response.json()["title"] == payload["title"]


@pytest.mark.asyncio
async def test_update_crisis(client):
    payload = {"title": "Test Crisis", "severity": "medium", "status": "detected", "category": "other"}
    response = await client.post("/api/v1/crisis/", json=payload)
    crisis_id = response.json()["id"]

    update = {"title": "Updated Crisis", "status": "assessing"}
    response = await client.put(f"/api/v1/crisis/{crisis_id}", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Crisis"
    assert data["status"] == "assessing"


@pytest.mark.asyncio
async def test_delete_crisis(client):
    payload = {"title": "Delete Me", "severity": "low", "status": "detected", "category": "other"}
    response = await client.post("/api/v1/crisis/", json=payload)
    crisis_id = response.json()["id"]

    response = await client.delete(f"/api/v1/crisis/{crisis_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/crisis/{crisis_id}")
    assert response.status_code == 404
