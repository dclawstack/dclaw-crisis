"""Prometheus metrics for DClaw Crisis (PRD §4 monitoring).

Three flavors:

- **HTTP** — request count + duration histogram by method/path/status.
  Path is the route template, not the concrete URL, so cardinality stays low
  (e.g. `/api/v1/crisis/{crisis_id}/summarize`, not
  `/api/v1/crisis/<uuid>/summarize`).
- **AI** — per-service call count + duration. Wraps each AI service via
  `time_ai_call(service)` async context manager.
- **LLM** — provider-level counters (openrouter / ollama / fallback) for
  raw call counts and failures.

`/metrics` is exposed via `routes/metrics.py` and uses the default registry.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


# ── HTTP layer ─────────────────────────────────────────────────────────────

http_requests_total = Counter(
    "dclaw_http_requests_total",
    "HTTP requests handled.",
    labelnames=("method", "route", "status"),
)
http_request_duration_seconds = Histogram(
    "dclaw_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "route"),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# ── AI services ─────────────────────────────────────────────────────────────

ai_calls_total = Counter(
    "dclaw_ai_calls_total",
    "AI service calls (one increment per logical service invocation).",
    labelnames=("service", "outcome"),  # outcome=success|error
)
ai_call_duration_seconds = Histogram(
    "dclaw_ai_call_duration_seconds",
    "AI service call latency.",
    labelnames=("service",),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# ── LLM provider layer ──────────────────────────────────────────────────────

llm_provider_calls_total = Counter(
    "dclaw_llm_provider_calls_total",
    "Raw LLM provider HTTP calls.",
    labelnames=("provider", "outcome"),  # outcome=ok|empty|error
)

# ── Cache + rate-limit + idempotency ────────────────────────────────────────

cache_events_total = Counter(
    "dclaw_cache_events_total",
    "Cache events.",
    labelnames=("event",),  # hit | miss | set | invalidate
)
rate_limit_blocks_total = Counter(
    "dclaw_rate_limit_blocks_total",
    "Requests blocked by the rate limiter.",
    labelnames=("scope",),
)
idempotency_replays_total = Counter(
    "dclaw_idempotency_replays_total",
    "Cached responses returned via Idempotency-Key.",
    labelnames=("scope",),
)


# ── Helpers ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def time_ai_call(service: str) -> AsyncIterator[None]:
    """Time an AI service call and emit duration + outcome counters."""
    start = time.perf_counter()
    outcome = "success"
    try:
        yield
    except Exception:
        outcome = "error"
        raise
    finally:
        elapsed = time.perf_counter() - start
        ai_call_duration_seconds.labels(service=service).observe(elapsed)
        ai_calls_total.labels(service=service, outcome=outcome).inc()


def metrics_payload() -> tuple[bytes, str]:
    """Render the current registry. Used by the /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
