"""HTTP request/duration metrics middleware.

Uses the route template (e.g. `/api/v1/crisis/{crisis_id}`) as the label
rather than the concrete path, so we don't blow up Prometheus with one label
per UUID.
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import http_request_duration_seconds, http_requests_total


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and hasattr(route, "path"):
        return route.path  # type: ignore[no-any-return]
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            elapsed = time.perf_counter() - start
            route = _route_template(request)
            method = request.method
            # Excluding /metrics from its own metrics avoids a tight loop
            # when Prometheus scrapes.
            if route != "/metrics":
                http_requests_total.labels(method=method, route=route, status=str(status_code)).inc()
                http_request_duration_seconds.labels(method=method, route=route).observe(elapsed)
        return response
