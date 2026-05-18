"""AI Playbook Advisor (PRD P1.4).

Given a resolved or contained Crisis, recommend concrete updates to the
closest-matching Playbook so the next crisis of the same kind benefits from
what we just learned. Recommendations are NEVER auto-applied — they're a
suggestion the operator reviews and selectively accepts.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crisis import Crisis
from app.models.playbook import Playbook
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis playbook advisor. Given a crisis that has just "
    "concluded and an existing playbook template that was (or could have been) "
    "used, suggest concrete, minimal updates to that playbook. Be conservative — "
    "only suggest changes the evidence in the crisis context actually supports.\n\n"
    "Output strict JSON only:\n"
    "{\n"
    '  "summary": "1-2 sentences explaining why these changes",\n'
    '  "suggested_changes": [\n'
    "    {\n"
    '      "kind": "add_step" | "rewrite_step" | "remove_step" | "change_role",\n'
    '      "step_order": int | null,  // existing step order for rewrite/remove/change_role; null for add_step\n'
    '      "new_title": string | null,\n'
    '      "new_description": string | null,\n'
    '      "new_role": string | null,\n'
    '      "rationale": string\n'
    "    },\n"
    "    ...\n"
    "  ]\n"
    "}\n\n"
    "If no meaningful changes are warranted, return an empty `suggested_changes` array."
)


async def _pick_closest_playbook(crisis: Crisis, db: AsyncSession) -> Playbook | None:
    """Find a playbook in the same category as the crisis. Picks the most recently updated."""
    stmt = (
        select(Playbook)
        .where(Playbook.category == crisis.category)
        .order_by(Playbook.updated_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def suggest_playbook_updates(crisis: Crisis, db: AsyncSession) -> dict:
    playbook = await _pick_closest_playbook(crisis, db)
    if playbook is None:
        return {
            "playbook_id": None,
            "playbook_name": None,
            "summary": f"No existing playbook in category '{crisis.category}' to update. Consider creating one.",
            "suggested_changes": [],
        }

    context = render_crisis_context(crisis, max_actions=50, max_comms=30)
    user = (
        f"Crisis just concluded (or in progress) — status: {crisis.status}.\n"
        f"Existing playbook to consider updating: {playbook.name} (id={playbook.id}).\n"
        f"Existing steps: {playbook.steps}\n\n"
        f"Crisis context:\n{context}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=1500)

    changes = data.get("suggested_changes") if isinstance(data, dict) else None
    if not isinstance(changes, list):
        changes = []

    cleaned: list[dict] = []
    allowed_kinds = {"add_step", "rewrite_step", "remove_step", "change_role"}
    for c in changes:
        if not isinstance(c, dict):
            continue
        kind = str(c.get("kind", "")).strip()
        if kind not in allowed_kinds:
            continue
        cleaned.append(
            {
                "kind": kind,
                "step_order": c.get("step_order") if isinstance(c.get("step_order"), int) else None,
                "new_title": _opt_str(c.get("new_title")),
                "new_description": _opt_str(c.get("new_description")),
                "new_role": _opt_str(c.get("new_role")),
                "rationale": str(c.get("rationale") or "").strip(),
            }
        )

    return {
        "playbook_id": playbook.id,
        "playbook_name": playbook.name,
        "summary": str(data.get("summary") or "").strip(),
        "suggested_changes": cleaned,
    }


def _opt_str(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None
