"""Client for DClaw Continuity BCP activation (PRD P2.2).

If `CONTINUITY_API_URL` is set, POSTs to that endpoint. Otherwise runs in
simulator mode and returns a stubbed acknowledgement so the rest of the flow
works in dev without the Continuity service running.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def activate_bcp(
    *,
    crisis_id: str,
    crisis_title: str,
    crisis_severity: str,
    crisis_category: str,
    bcp_plan_id: str | None,
    bcp_plan_name: str | None,
    notes: str | None,
) -> dict:
    """Returns {provider, status, response_payload, error_message?}.

    Never raises — failure becomes status='failed' so the caller can persist
    the attempt and surface to the operator.
    """
    payload = {
        "crisis": {
            "id": crisis_id,
            "title": crisis_title,
            "severity": crisis_severity,
            "category": crisis_category,
        },
        "bcp_plan_id": bcp_plan_id,
        "bcp_plan_name": bcp_plan_name,
        "notes": notes,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    url = settings.continuity_api_url
    if not url:
        logger.info("continuity.simulator: stub activation for crisis=%s", crisis_id)
        return {
            "provider": "simulator",
            "status": "activated",
            "response_payload": {
                "stub": True,
                "message": "Continuity service not configured (CONTINUITY_API_URL unset); returning simulator acknowledgement.",
                "would_post_to": "<unset>",
                "request": payload,
            },
            "error_message": None,
        }

    headers = {"Content-Type": "application/json"}
    if settings.continuity_api_key:
        headers["Authorization"] = f"Bearer {settings.continuity_api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url.rstrip("/") + "/activations", headers=headers, json=payload)
            resp.raise_for_status()
            return {
                "provider": "dclaw-continuity",
                "status": "activated",
                "response_payload": resp.json() if resp.content else {},
                "error_message": None,
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("continuity API call failed: %s", exc)
        return {
            "provider": "dclaw-continuity",
            "status": "failed",
            "response_payload": {"request": payload},
            "error_message": str(exc),
        }
