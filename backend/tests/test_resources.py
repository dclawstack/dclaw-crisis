import pytest


@pytest.mark.asyncio
async def test_create_and_get_resource(client):
    payload = {
        "name": "Boston War Room A",
        "resource_type": "war_room",
        "status": "available",
        "capacity": "12 people",
        "location": "HQ, floor 4",
        "attributes": {"av": "yes", "secure": True},
    }
    res = await client.post("/api/v1/resources/", json=payload)
    assert res.status_code == 201
    rid = res.json()["id"]

    res = await client.get(f"/api/v1/resources/{rid}")
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Boston War Room A"
    assert body["attributes"]["secure"] is True


@pytest.mark.asyncio
async def test_filter_by_status(client):
    await client.post("/api/v1/resources/", json={"name": "A", "resource_type": "equipment", "status": "available"})
    await client.post("/api/v1/resources/", json={"name": "B", "resource_type": "equipment", "status": "in_use"})

    res = await client.get("/api/v1/resources/?status=available")
    assert all(r["status"] == "available" for r in res.json())
    assert len(res.json()) == 1


@pytest.mark.asyncio
async def test_filter_by_type(client):
    await client.post("/api/v1/resources/", json={"name": "Slack #ir", "resource_type": "comm_channel"})
    await client.post("/api/v1/resources/", json={"name": "AWS support", "resource_type": "vendor_contact"})

    res = await client.get("/api/v1/resources/?resource_type=comm_channel")
    assert all(r["resource_type"] == "comm_channel" for r in res.json())
    assert len(res.json()) == 1


@pytest.mark.asyncio
async def test_update_and_delete_resource(client):
    rid = (await client.post("/api/v1/resources/", json={"name": "X", "resource_type": "other"})).json()["id"]
    upd = await client.put(f"/api/v1/resources/{rid}", json={"status": "in_use", "notes": "Allocated to incident #12"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "in_use"
    assert upd.json()["notes"] == "Allocated to incident #12"

    delr = await client.delete(f"/api/v1/resources/{rid}")
    assert delr.status_code == 204
    assert (await client.get(f"/api/v1/resources/{rid}")).status_code == 404
