import pytest


@pytest.mark.asyncio
async def test_dashboard_stats(client):
    response = await client.get("/api/v1/dashboard/")
    assert response.status_code == 200
    data = response.json()
    assert "active_crises" in data
    assert "open_action_items" in data
    assert "critical_crises" in data
    assert "avg_resolution_hours" in data
    assert "severity_breakdown" in data
    assert "status_breakdown" in data
