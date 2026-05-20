"""Render exportable artifacts (legal hold notices, crisis post-mortems)."""
from __future__ import annotations

from app.models.crisis import Crisis
from app.models.legal_hold import LegalHold


def render_legal_hold_notice(hold: LegalHold) -> str:
    lines: list[str] = []
    lines.append("LEGAL HOLD NOTICE")
    lines.append("=" * 60)
    lines.append(f"Title: {hold.title}")
    if hold.crisis_id:
        lines.append(f"Related crisis ID: {hold.crisis_id}")
    if hold.issued_at:
        lines.append(f"Issued: {hold.issued_at.isoformat()}")
    if hold.issued_by:
        lines.append(f"Issued by: {hold.issued_by}")
    lines.append(f"Status: {hold.status}")
    lines.append("")

    if hold.scope_description:
        lines.append("SCOPE")
        lines.append("-" * 60)
        lines.append(hold.scope_description)
        lines.append("")

    if hold.custodians:
        lines.append("CUSTODIANS")
        lines.append("-" * 60)
        for c in hold.custodians:
            name = c.get("name") or "(unnamed)"
            email = c.get("email") or ""
            role = c.get("role") or ""
            extras = " ".join(p for p in [email, f"({role})" if role else ""] if p)
            lines.append(f"- {name} {extras}".rstrip())
        lines.append("")

    if hold.data_sources:
        lines.append("DATA SOURCES TO PRESERVE")
        lines.append("-" * 60)
        for ds in hold.data_sources:
            lines.append(f"- {ds}")
        lines.append("")

    if hold.hold_notice_text:
        lines.append("NOTICE TEXT")
        lines.append("-" * 60)
        lines.append(hold.hold_notice_text)
        lines.append("")

    if hold.released_at:
        lines.append(f"Released: {hold.released_at.isoformat()}")
        if hold.release_reason:
            lines.append(f"Release reason: {hold.release_reason}")

    return "\n".join(lines)


def render_post_mortem_markdown(crisis: Crisis, post_mortem: dict) -> str:
    parts: list[str] = []
    parts.append(f"# Post-Mortem: {crisis.title}")
    parts.append("")
    parts.append(f"- **Severity:** {crisis.severity}")
    parts.append(f"- **Category:** {crisis.category}")
    parts.append(f"- **Status at export:** {crisis.status}")
    parts.append(f"- **Detected:** {crisis.detected_at.isoformat() if crisis.detected_at else '—'}")
    if crisis.resolved_at:
        parts.append(f"- **Resolved:** {crisis.resolved_at.isoformat()}")
    if post_mortem.get("is_speculative"):
        parts.append("")
        parts.append("> ⚠ This post-mortem is flagged as **speculative** — context was thin when generated.")
    parts.append("")

    parts.append("## Timeline")
    parts.append(post_mortem.get("timeline_summary") or "(none)")
    parts.append("")

    parts.append("## Root cause")
    parts.append(post_mortem.get("root_cause") or "(none)")
    parts.append("")

    parts.append("## What went well")
    for item in post_mortem.get("what_went_well") or []:
        parts.append(f"- {item}")
    if not post_mortem.get("what_went_well"):
        parts.append("- (none recorded)")
    parts.append("")

    parts.append("## What went poorly")
    for item in post_mortem.get("what_went_poorly") or []:
        parts.append(f"- {item}")
    if not post_mortem.get("what_went_poorly"):
        parts.append("- (none recorded)")
    parts.append("")

    parts.append("## Lessons learned")
    for item in post_mortem.get("lessons_learned") or []:
        parts.append(f"- {item}")
    if not post_mortem.get("lessons_learned"):
        parts.append("- (none recorded)")
    parts.append("")

    return "\n".join(parts)
