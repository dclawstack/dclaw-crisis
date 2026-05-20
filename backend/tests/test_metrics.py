"""Tests for the Prometheus metrics endpoint and middleware."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(client):
    res = await client.get("/metrics")
    assert res.status_code == 200
    body = res.text
    # Default exposition format opens with HELP/TYPE comments.
    assert "# HELP" in body
    assert "# TYPE" in body
    # Our custom metric names must appear.
    assert "dclaw_http_requests_total" in body
    assert "dclaw_http_request_duration_seconds" in body
    assert "dclaw_ai_calls_total" in body


@pytest.mark.asyncio
async def test_http_middleware_records_request_counters(client):
    # Hit a known route then assert the counter appears.
    await client.get("/api/v1/crisis/")
    res = await client.get("/metrics")
    body = res.text
    # Route template (with the {var} pattern) is preserved as a label.
    assert 'route="/api/v1/crisis/"' in body
    assert 'status="200"' in body


@pytest.mark.asyncio
async def test_metrics_endpoint_does_not_record_itself(client):
    # Scrape twice and make sure no `route="/metrics"` label appears.
    await client.get("/metrics")
    res = await client.get("/metrics")
    assert 'route="/metrics"' not in res.text


@pytest.mark.asyncio
async def test_time_ai_call_records_outcome():
    from app.core.metrics import time_ai_call, ai_calls_total

    before = ai_calls_total.labels(service="unit_test", outcome="success")._value.get()
    async with time_ai_call("unit_test"):
        pass
    after = ai_calls_total.labels(service="unit_test", outcome="success")._value.get()
    assert after == before + 1


@pytest.mark.asyncio
async def test_time_ai_call_records_error_on_exception():
    from app.core.metrics import time_ai_call, ai_calls_total

    before = ai_calls_total.labels(service="unit_test_err", outcome="error")._value.get()
    with pytest.raises(RuntimeError):
        async with time_ai_call("unit_test_err"):
            raise RuntimeError("boom")
    after = ai_calls_total.labels(service="unit_test_err", outcome="error")._value.get()
    assert after == before + 1


@pytest.mark.asyncio
async def test_ai_call_metric_increments_when_summarize_runs(client, monkeypatch):
    """Wired end-to-end: hitting /summarize bumps dclaw_ai_calls_total{service=summarize}."""
    from app.services import ai_summarizer
    from app.core.metrics import ai_calls_total

    class FakeRes:
        def __init__(self, t): self.text = t

    async def fake_complete(system, user, *, temperature=0.3, max_tokens=800):
        return FakeRes("summary text")
    monkeypatch.setattr(ai_summarizer, "complete", fake_complete)

    before = ai_calls_total.labels(service="summarize", outcome="success")._value.get()

    cid = (await client.post(
        "/api/v1/crisis/",
        json={"title": "metrics", "severity": "low", "status": "detected", "category": "other"},
    )).json()["id"]
    res = await client.post(f"/api/v1/crisis/{cid}/summarize")
    assert res.status_code == 200

    after = ai_calls_total.labels(service="summarize", outcome="success")._value.get()
    assert after == before + 1
