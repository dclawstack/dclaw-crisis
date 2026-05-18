"""AI Resource Matcher (PRD P1.3).

Given a crisis and the org's resource inventory, recommend which resources
to deploy. Considers status (available vs in-use), resource type, capacity,
and the nature of the crisis.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crisis import Crisis
from app.models.resource import Resource
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis resource mobilization strategist. Given a "
    "crisis and an inventory of resources, recommend which to deploy. "
    "Prefer resources with status 'available'. If you recommend a resource "
    "that's already in use, flag the conflict clearly. Output strict JSON.\n\n"
    "Output schema:\n"
    "{\n"
    '  "recommendations": [\n'
    "    {\n"
    '      "resource_id": str,\n'
    '      "fit_score": float 0.0-1.0,\n'
    '      "deploy_now": true | false,\n'
    '      "reason": "1-2 sentence reason",\n'
    '      "conflict_note": "if resource is in-use/unavailable, brief note about the conflict; else null"\n'
    "    },\n"
    "    ...\n"
    "  ],\n"
    '  "gaps": ["resource types or capabilities the org is missing for this crisis", ...]\n'
    "}\n"
    "Rules:\n"
    "- Only include resources whose fit_score >= 0.3.\n"
    "- Sort recommendations by fit_score descending.\n"
    "- Be honest about gaps — say what's missing rather than over-recommending what's available."
)


async def match_resources(crisis: Crisis, db: AsyncSession) -> dict:
    stmt = select(Resource).order_by(Resource.status, Resource.name).limit(200)
    res = await db.execute(stmt)
    resources = list(res.scalars().all())
    if not resources:
        return {
            "recommendations": [],
            "gaps": ["No resources registered. Add resources before asking for recommendations."],
        }

    by_id = {r.id: r for r in resources}
    inventory = [
        {
            "id": r.id,
            "name": r.name,
            "type": r.resource_type,
            "status": r.status,
            "capacity": r.capacity,
            "location": r.location,
            "attributes": r.attributes,
        }
        for r in resources
    ]

    context = render_crisis_context(crisis, max_actions=20, max_comms=10)
    user = (
        f"Crisis snapshot:\n{context}\n\n"
        f"Resource inventory ({len(inventory)} resources):\n{inventory}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=1800)

    recs_raw = data.get("recommendations") if isinstance(data, dict) else None
    cleaned: list[dict] = []
    if isinstance(recs_raw, list):
        for r in recs_raw:
            if not isinstance(r, dict):
                continue
            rid = r.get("resource_id")
            if rid not in by_id:
                continue
            try:
                fit = max(0.0, min(1.0, float(r.get("fit_score", 0.0))))
            except (TypeError, ValueError):
                fit = 0.0
            if fit < 0.3:
                continue
            resource = by_id[rid]
            cleaned.append(
                {
                    "resource_id": rid,
                    "resource_name": resource.name,
                    "resource_type": resource.resource_type,
                    "current_status": resource.status,
                    "fit_score": fit,
                    "deploy_now": bool(r.get("deploy_now", False)),
                    "reason": str(r.get("reason") or "").strip(),
                    "conflict_note": _opt_str(r.get("conflict_note")),
                }
            )

    cleaned.sort(key=lambda x: x["fit_score"], reverse=True)

    gaps_raw = data.get("gaps") if isinstance(data, dict) else None
    gaps = [str(g).strip() for g in gaps_raw if str(g).strip()] if isinstance(gaps_raw, list) else []

    return {"recommendations": cleaned, "gaps": gaps}


def _opt_str(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "null" else None
