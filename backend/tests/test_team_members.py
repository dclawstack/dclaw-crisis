import pytest


@pytest.mark.asyncio
async def test_list_team_members(client):
    response = await client.get("/api/v1/team-members/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_get_team_member(client):
    payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "role": "Incident Commander",
        "department": "Operations",
        "phone": "+1-555-0100",
    }
    response = await client.post("/api/v1/team-members/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    member_id = data["id"]

    response = await client.get(f"/api/v1/team-members/{member_id}")
    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]


@pytest.mark.asyncio
async def test_update_team_member(client):
    payload = {"name": "Bob", "email": "bob@example.com", "role": "Analyst"}
    response = await client.post("/api/v1/team-members/", json=payload)
    member_id = response.json()["id"]

    update = {"role": "Senior Analyst", "is_active": False}
    response = await client.put(f"/api/v1/team-members/{member_id}", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Senior Analyst"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_team_member(client):
    payload = {"name": "Charlie", "email": "charlie@example.com", "role": "Legal"}
    response = await client.post("/api/v1/team-members/", json=payload)
    member_id = response.json()["id"]

    response = await client.delete(f"/api/v1/team-members/{member_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/team-members/{member_id}")
    assert response.status_code == 404
