"""AI Next-Best-Action Recommender."""
from __future__ import annotations

from app.models.crisis import Crisis
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis AI Copilot. Given a crisis snapshot, recommend the single "
    "highest-leverage next action the response team should take. Respond ONLY with valid JSON "
    "matching this schema: {\"title\": str, \"description\": str, \"priority\": \"critical|high|medium|low\", "
    "\"rationale\": str, \"suggested_assignee_role\": str}. Keep title under 80 chars. "
    "Do not include action items that are already pending or in progress."
)


async def recommend_next_action(crisis: Crisis) -> dict:
    context = render_crisis_context(crisis)
    user = f"Recommend the next-best-action for this crisis:\n\n{context}"
    return await complete_json(SYSTEM_PROMPT, user, temperature=0.3, max_tokens=400)
