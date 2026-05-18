"""AI Crisis Copilot — contextual chat assistant for the operations team.

Per REVISED-PRD.md §9: contextually aware of domain data, suggests next actions,
falls back to local Ollama when cloud is unavailable.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_item import ActionItem, ActionItemStatus
from app.models.crisis import Crisis, CrisisStatus
from app.services.crisis_context import render_crisis_context
from app.services.llm import ChatMessage, chat

SYSTEM_PROMPT = (
    "You are the DClaw Crisis AI Copilot. You help operations, legal, PR, and security "
    "teams coordinate crisis response. You have read access to the live crisis database. "
    "Use the provided 'OPERATIONAL CONTEXT' to ground your answers. "
    "Always: (1) be concise, (2) suggest concrete next actions when relevant, "
    "(3) reference specific crises and action items by title when relevant, "
    "(4) never invent data — if context is missing, say so."
)

ACTIVE_STATUSES = (
    CrisisStatus.detected,
    CrisisStatus.assessing,
    CrisisStatus.responding,
)


async def _load_active_context(db: AsyncSession, *, focused_crisis_id: str | None = None) -> str:
    parts: list[str] = []

    if focused_crisis_id:
        focused = await db.get(Crisis, focused_crisis_id)
        if focused:
            parts.append("FOCUSED CRISIS:")
            parts.append(render_crisis_context(focused))
            parts.append("")

    active_stmt = (
        select(Crisis)
        .where(Crisis.status.in_([s.value for s in ACTIVE_STATUSES]))
        .order_by(Crisis.severity, Crisis.detected_at.desc())
        .limit(10)
    )
    res = await db.execute(active_stmt)
    active = [c for c in res.scalars().all() if c.id != focused_crisis_id]

    if active:
        parts.append("OTHER ACTIVE CRISES:")
        for c in active:
            parts.append(
                f"- [{c.severity}/{c.status}] {c.title} (id={c.id}) — {len(c.action_items)} actions"
            )
        parts.append("")

    overdue_stmt = (
        select(ActionItem)
        .where(ActionItem.status.in_([ActionItemStatus.pending.value, ActionItemStatus.in_progress.value, ActionItemStatus.blocked.value]))
        .order_by(ActionItem.due_at.asc())
        .limit(10)
    )
    res = await db.execute(overdue_stmt)
    open_actions = list(res.scalars().all())
    if open_actions:
        parts.append("OPEN ACTION ITEMS (top 10 by due date):")
        for a in open_actions:
            due = a.due_at.isoformat() if a.due_at else "no due date"
            parts.append(f"- [{a.priority}/{a.status}] {a.title} — due {due}")

    if not parts:
        return "No active crises or open action items."
    return "\n".join(parts)


async def copilot_chat(
    db: AsyncSession,
    messages: list[ChatMessage],
    *,
    focused_crisis_id: str | None = None,
) -> str:
    context_text = await _load_active_context(db, focused_crisis_id=focused_crisis_id)
    system_messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="system", content=f"OPERATIONAL CONTEXT:\n{context_text}"),
    ]
    res = await chat(system_messages + messages, temperature=0.4, max_tokens=900)
    return res.text.strip()
