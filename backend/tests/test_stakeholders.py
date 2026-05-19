import pytest


@pytest.mark.asyncio
async def test_create_and_list_stakeholder(client):
    payload = {
        "name": "Acme Corp Procurement",
        "type": "customer",
        "organization": "Acme Corp",
        "importance": "high",
        "email": "ops@acme.example",
        "tags": ["enterprise", "us-east"],
    }
    res = await client.post("/api/v1/stakeholders/", json=payload)
    assert res.status_code == 201
    sid = res.json()["id"]

    res = await client.get(f"/api/v1/stakeholders/{sid}")
    assert res.status_code == 200
    assert res.json()["name"] == "Acme Corp Procurement"
    assert res.json()["tags"] == ["enterprise", "us-east"]


@pytest.mark.asyncio
async def test_filter_by_type(client):
    await client.post("/api/v1/stakeholders/", json={"name": "Press A", "type": "media", "importance": "medium"})
    await client.post("/api/v1/stakeholders/", json={"name": "Bank", "type": "investor", "importance": "high"})

    res = await client.get("/api/v1/stakeholders/?type=media")
    assert res.status_code == 200
    assert all(s["type"] == "media" for s in res.json())
    assert len(res.json()) == 1


@pytest.mark.asyncio
async def test_active_only_filter(client):
    await client.post("/api/v1/stakeholders/", json={"name": "Active", "type": "internal", "is_active": True})
    await client.post("/api/v1/stakeholders/", json={"name": "Inactive", "type": "internal", "is_active": False})

    res = await client.get("/api/v1/stakeholders/?active_only=true")
    names = {s["name"] for s in res.json()}
    assert "Active" in names
    assert "Inactive" not in names


@pytest.mark.asyncio
async def test_update_and_delete_stakeholder(client):
    sid = (await client.post("/api/v1/stakeholders/", json={"name": "X", "type": "other"})).json()["id"]
    upd = await client.put(f"/api/v1/stakeholders/{sid}", json={"importance": "critical"})
    assert upd.status_code == 200
    assert upd.json()["importance"] == "critical"

    delr = await client.delete(f"/api/v1/stakeholders/{sid}")
    assert delr.status_code == 204
    assert (await client.get(f"/api/v1/stakeholders/{sid}")).status_code == 404
