"""AI Communication Draft Generator."""
from __future__ import annotations

from app.models.crisis import Crisis
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete

SYSTEM_PROMPT = (
    "You are the DClaw Crisis AI Copilot. Draft a crisis communication that is clear, "
    "empathetic, and factually grounded. Match the tone to the audience: internal updates "
    "are direct, stakeholder alerts are reassuring, public statements are measured, "
    "exec briefs are dense and quantitative. Never speculate or admit liability. "
    "Return the message body only — no preamble, no markdown headers."
)


async def draft_communication(
    crisis: Crisis,
    *,
    comm_type: str,
    channel: str,
    audience: str | None = None,
    extra_context: str | None = None,
) -> str:
    context = render_crisis_context(crisis)
    parts = [
        f"Draft a {comm_type} communication for the {channel} channel.",
        f"Audience: {audience}" if audience else None,
        f"Additional context from user: {extra_context}" if extra_context else None,
        "",
        "Crisis snapshot:",
        context,
    ]
    user = "\n".join(p for p in parts if p is not None)
    res = await complete(SYSTEM_PROMPT, user, temperature=0.5, max_tokens=600)
    return res.text.strip()
