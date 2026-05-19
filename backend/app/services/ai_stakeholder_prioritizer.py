"""AI Stakeholder Prioritizer (PRD P1.2).

Given a crisis and the org's stakeholder roster, rank which stakeholders need
to be notified, when, and through what channel, with talking points the
operator can copy into a communication.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crisis import Crisis
from app.models.stakeholder import Stakeholder
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis stakeholder communications strategist. Given a "
    "crisis and a roster of stakeholders, rank which need to be contacted, "
    "when, and how. Be conservative — only include stakeholders the evidence "
    "actually warrants. Output strict JSON only.\n\n"
    "Output schema:\n"
    "{\n"
    '  "priorities": [\n'
    "    {\n"
    '      "stakeholder_id": str,\n'
    '      "urgency": "immediate" | "within_4h" | "within_24h" | "post_resolution" | "not_required",\n'
    '      "channel": "phone" | "email" | "in_person" | "press_release" | "regulator_filing" | "other",\n'
    '      "talking_points": ["concise factual point", ...],\n'
    '      "rationale": "1-2 sentence why"\n'
    "    },\n"
    "    ...\n"
    "  ],\n"
    '  "notes": "1-2 sentences with anything the operator should know across all stakeholders"\n'
    "}\n"
    "Rules:\n"
    "- Only include stakeholders whose urgency is not 'not_required'.\n"
    "- Order priorities by urgency (immediate first).\n"
    "- Cap talking_points at 4 per stakeholder."
)


_VALID_URGENCY = {"immediate", "within_4h", "within_24h", "post_resolution", "not_required"}
_VALID_CHANNEL = {"phone", "email", "in_person", "press_release", "regulator_filing", "other"}


async def prioritize_stakeholders(crisis: Crisis, db: AsyncSession) -> dict:
    stmt = (
        select(Stakeholder)
        .where(Stakeholder.is_active.is_(True))
        .order_by(Stakeholder.importance, Stakeholder.name)
        .limit(200)
    )
    res = await db.execute(stmt)
    stakeholders = list(res.scalars().all())
    if not stakeholders:
        return {
            "priorities": [],
            "notes": "No active stakeholders are registered. Add stakeholders before asking for priorities.",
        }

    by_id = {s.id: s for s in stakeholders}
    roster = [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "organization": s.organization,
            "importance": s.importance,
            "tags": s.tags,
        }
        for s in stakeholders
    ]

    context = render_crisis_context(crisis, max_actions=20, max_comms=10)
    user = (
        f"Crisis snapshot:\n{context}\n\n"
        f"Stakeholder roster ({len(roster)} active):\n{roster}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=2000)

    priorities_raw = data.get("priorities") if isinstance(data, dict) else None
    cleaned: list[dict] = []
    if isinstance(priorities_raw, list):
        for p in priorities_raw:
            if not isinstance(p, dict):
                continue
            sid = p.get("stakeholder_id")
            if sid not in by_id:
                continue
            urgency = str(p.get("urgency", "")).lower()
            if urgency not in _VALID_URGENCY or urgency == "not_required":
                continue
            channel = str(p.get("channel", "email")).lower()
            if channel not in _VALID_CHANNEL:
                channel = "other"
            tp = p.get("talking_points") or []
            if not isinstance(tp, list):
                tp = []
            tp = [str(t).strip() for t in tp if str(t).strip()][:4]

            s = by_id[sid]
            cleaned.append(
                {
                    "stakeholder_id": sid,
                    "stakeholder_name": s.name,
                    "stakeholder_type": s.type,
                    "organization": s.organization,
                    "urgency": urgency,
                    "channel": channel,
                    "talking_points": tp,
                    "rationale": str(p.get("rationale") or "").strip(),
                }
            )

    # Order by urgency for the UI.
    order = {"immediate": 0, "within_4h": 1, "within_24h": 2, "post_resolution": 3}
    cleaned.sort(key=lambda x: order.get(x["urgency"], 9))

    return {
        "priorities": cleaned,
        "notes": str(data.get("notes") or "").strip(),
    }
