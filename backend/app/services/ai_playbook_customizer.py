"""Tailor a playbook's steps to a specific incident context (PRD P0.3).

When an operator instantiates a playbook with extra `incident_context`,
this service rewrites each step's title/description to be specific to that
incident — replacing generic language with concrete, incident-specific
phrasing while preserving step order and original suggested roles.
"""
from __future__ import annotations

from app.models.playbook import Playbook
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis playbook customization assistant. You receive a "
    "generic crisis-response playbook and a brief description of a specific "
    "incident. Rewrite each step so it is concrete and incident-specific, "
    "while preserving the original intent and the suggested role.\n\n"
    "Rules:\n"
    "- Keep the same number of steps, in the same order.\n"
    "- Keep `suggested_assignee_role` exactly as in the input.\n"
    "- Make titles short (under 100 chars) and action-oriented.\n"
    "- Make descriptions specific to the incident (mention systems, parties, regulators, etc. when relevant).\n"
    "- Do NOT add or remove steps.\n"
    "- Output strict JSON only.\n\n"
    "Output schema:\n"
    "{\n"
    '  "steps": [ {"order": int, "title": str, "description": str, "suggested_assignee_role": str | null}, ... ]\n'
    "}"
)


async def customize_steps(playbook: Playbook, incident_context: str) -> list[dict]:
    """Return a list of customized step dicts. Raises on LLM/JSON errors."""
    steps_in = []
    for step in sorted(playbook.steps or [], key=lambda s: s.get("order", 0)):
        steps_in.append(
            {
                "order": step.get("order"),
                "title": step.get("title"),
                "description": step.get("description"),
                "suggested_assignee_role": step.get("suggested_assignee_role"),
            }
        )

    user = (
        f"Playbook: {playbook.name}\n"
        f"Category: {playbook.category}\n"
        f"Generic description: {playbook.description or ''}\n\n"
        f"Incident context (from operator):\n{incident_context.strip()}\n\n"
        f"Generic steps to customize:\n"
        f"{steps_in}"
    )

    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.3, max_tokens=2000)
    steps_out = data.get("steps") if isinstance(data, dict) else None
    if not isinstance(steps_out, list) or len(steps_out) != len(steps_in):
        # Model didn't follow the schema — fall back to originals.
        return steps_in

    # Validate + sanitize each output step against the corresponding input.
    cleaned: list[dict] = []
    for original, customized in zip(steps_in, steps_out):
        if not isinstance(customized, dict):
            cleaned.append(original)
            continue
        cleaned.append(
            {
                "order": original["order"],
                "title": str(customized.get("title") or original["title"])[:255],
                "description": str(customized.get("description") or original.get("description") or ""),
                # Always preserve the original role to avoid drift.
                "suggested_assignee_role": original.get("suggested_assignee_role"),
            }
        )
    return cleaned
