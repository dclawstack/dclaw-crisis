"""AI Scenario Generator (PRD P2.1) — produces tabletop simulation scenarios."""
from __future__ import annotations

from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis simulation designer. Given a category and severity, "
    "produce a realistic tabletop scenario the response team can run through. Be "
    "specific — use concrete timestamps, system names, and stakeholders so the "
    "participants have something to react to.\n\n"
    "Output strict JSON:\n"
    "{\n"
    '  "scenario": "3-5 paragraph narrative of an unfolding incident with specific facts and a clear escalation arc",\n'
    '  "expected_actions": [\n'
    "    {\"order\": int, \"action\": \"what the team should do\", \"role\": \"who owns it\"}, ...\n"
    "  ],\n"
    '  "expected_outcomes": ["measurable success criteria", ...],\n'
    '  "twist_at_minute_30": "a complication that arrives mid-exercise"\n'
    "}\n"
    "Rules:\n"
    "- 5-10 expected_actions, ordered by when they should happen.\n"
    "- 3-5 expected_outcomes.\n"
    "- Twist should genuinely shift response priorities, not just add work."
)


async def generate_scenario(scenario_type: str, severity: str, custom_seed: str | None = None) -> dict:
    user = (
        f"Generate a tabletop simulation scenario.\n"
        f"Category: {scenario_type}\n"
        f"Severity: {severity}\n"
    )
    if custom_seed:
        user += f"\nAdditional seed/context from operator: {custom_seed}"
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.7, max_tokens=2000)

    actions_raw = data.get("expected_actions") if isinstance(data, dict) else None
    actions: list[dict] = []
    if isinstance(actions_raw, list):
        for a in actions_raw:
            if not isinstance(a, dict):
                continue
            actions.append(
                {
                    "order": int(a.get("order")) if str(a.get("order", "")).isdigit() else len(actions) + 1,
                    "action": str(a.get("action") or "").strip(),
                    "role": str(a.get("role") or "").strip(),
                }
            )
    actions.sort(key=lambda x: x["order"])

    outcomes_raw = data.get("expected_outcomes") if isinstance(data, dict) else None
    outcomes = [str(o).strip() for o in outcomes_raw if str(o).strip()] if isinstance(outcomes_raw, list) else []

    twist = str(data.get("twist_at_minute_30") or "").strip()
    scenario_text = str(data.get("scenario") or "").strip()
    if twist:
        scenario_text += f"\n\n— At T+30 minutes: {twist}"

    return {
        "scenario": scenario_text,
        "expected_actions": actions,
        "expected_outcomes": outcomes,
    }
