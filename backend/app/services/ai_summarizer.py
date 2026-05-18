"""AI Crisis Summarizer — generates an executive summary of a Crisis."""
from __future__ import annotations

from app.models.crisis import Crisis
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete

SYSTEM_PROMPT = (
    "You are the DClaw Crisis AI Copilot. Produce concise executive summaries of "
    "active crises for senior leadership. Be factual, neutral, and action-oriented. "
    "Always include: (1) what happened, (2) current status and severity, "
    "(3) top 3 in-flight actions, (4) blockers or risks, (5) next 24h focus. "
    "Use markdown with short bullet points. Do not invent facts."
)


async def summarize_crisis(crisis: Crisis) -> str:
    context = render_crisis_context(crisis)
    user = f"Summarize the following crisis for the leadership team.\n\n{context}"
    res = await complete(SYSTEM_PROMPT, user, temperature=0.3, max_tokens=800)
    return res.text.strip()
