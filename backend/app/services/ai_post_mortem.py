"""AI Post-Crisis Review service (PRD P1.4).

Given a (preferably resolved) Crisis, produce a structured post-mortem:
- chronological timeline summary
- what went well
- what went poorly
- probable root cause
- a list of distinct lessons learned

Works best when the crisis has action items and communications populated.
Returns a dict shaped for the API endpoint to return directly.
"""
from __future__ import annotations

from app.core.cache import cache_get_or_set
from app.core.metrics import time_ai_call
from app.models.crisis import Crisis
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis post-mortem analyst. Given a snapshot of a crisis "
    "and its response (action items + communications), produce a structured "
    "post-mortem suitable for an executive blameless review. Be specific, "
    "evidence-based, and avoid platitudes. Output strict JSON only.\n\n"
    "Output schema:\n"
    "{\n"
    '  "timeline_summary": "3-5 sentence narrative of what happened, in order",\n'
    '  "what_went_well": ["concrete observation", ...],\n'
    '  "what_went_poorly": ["concrete observation", ...],\n'
    '  "root_cause": "1-3 sentences identifying the probable underlying cause",\n'
    '  "lessons_learned": ["actionable lesson", ...],\n'
    '  "is_speculative": true | false  // true if context is too thin for high confidence\n'
    "}"
)


async def generate_post_mortem(crisis: Crisis) -> dict:
    cache_key = f"ai:post-mortem:{crisis.id}:{crisis.updated_at.isoformat()}"
    return await cache_get_or_set(cache_key, None, lambda: _run_post_mortem(crisis))


async def _run_post_mortem(crisis: Crisis) -> dict:
    async with time_ai_call("post_mortem"):
        return await _do_post_mortem(crisis)


async def _do_post_mortem(crisis: Crisis) -> dict:
    context = render_crisis_context(crisis, max_actions=50, max_comms=30)
    user = (
        f"Produce a post-mortem for the following crisis.\n"
        f"Current status: {crisis.status}\n\n"
        f"{context}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=1500)

    # Defensive shaping so the API never returns malformed JSON.
    return {
        "timeline_summary": str(data.get("timeline_summary") or "").strip(),
        "what_went_well": _as_list(data.get("what_went_well")),
        "what_went_poorly": _as_list(data.get("what_went_poorly")),
        "root_cause": str(data.get("root_cause") or "").strip(),
        "lessons_learned": _as_list(data.get("lessons_learned")),
        "is_speculative": bool(data.get("is_speculative", False)),
    }


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
