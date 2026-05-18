"""Build prompt-ready text snapshots of a Crisis for the AI services."""
from __future__ import annotations

from app.models.crisis import Crisis


def render_crisis_context(crisis: Crisis, *, max_actions: int = 25, max_comms: int = 15) -> str:
    """Return a human/LLM-readable summary of a Crisis with its actions and recent comms."""
    lines: list[str] = []
    lines.append(f"Crisis: {crisis.title}")
    lines.append(f"Severity: {crisis.severity} | Status: {crisis.status} | Category: {crisis.category}")
    if crisis.description:
        lines.append(f"Description: {crisis.description}")
    if crisis.estimated_impact_usd:
        lines.append(f"Estimated impact (USD): {crisis.estimated_impact_usd:,.0f}")
    lines.append(f"Detected at: {crisis.detected_at.isoformat()}")
    if crisis.lead:
        lines.append(f"Lead: {crisis.lead.name} ({crisis.lead.role})")
    if crisis.resolved_at:
        lines.append(f"Resolved at: {crisis.resolved_at.isoformat()}")

    actions = sorted(
        crisis.action_items,
        key=lambda a: (a.priority != "critical", a.status == "completed", a.created_at),
    )[:max_actions]
    if actions:
        lines.append("")
        lines.append("Action items:")
        for a in actions:
            assignee = a.assignee.name if a.assignee else "unassigned"
            due = f", due {a.due_at.isoformat()}" if a.due_at else ""
            lines.append(
                f"- [{a.status}] ({a.priority}) {a.title} — assignee: {assignee}{due}"
            )

    comms = sorted(crisis.communications, key=lambda c: c.created_at, reverse=True)[:max_comms]
    if comms:
        lines.append("")
        lines.append("Recent communications (newest first):")
        for c in comms:
            author = c.author.name if c.author else "system"
            lines.append(
                f"- [{c.created_at.isoformat()}] {c.comm_type}/{c.channel} by {author}: {c.message[:200]}"
            )

    return "\n".join(lines)
