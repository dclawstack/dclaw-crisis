"""Seed playbook templates for PRD P0.3 Response Planning.

Provides 5 baseline templates (data breach, outage, exec issue, PR crisis, safety incident).
Idempotent: existing playbooks with the same name are skipped.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.playbook import Playbook

SEED_TEMPLATES: list[dict] = [
    {
        "name": "Data Breach Response",
        "category": "security",
        "description": "Standard response for a confirmed or suspected data breach.",
        "steps": [
            {"order": 1, "title": "Contain — isolate affected systems", "description": "Disconnect compromised hosts; rotate credentials.", "suggested_assignee_role": "security_lead"},
            {"order": 2, "title": "Preserve evidence", "description": "Snapshot affected hosts and logs.", "suggested_assignee_role": "forensics"},
            {"order": 3, "title": "Notify legal & compliance", "description": "Engage general counsel; determine regulatory reporting clock.", "suggested_assignee_role": "general_counsel"},
            {"order": 4, "title": "Assess scope", "description": "Identify what data, which users, what time window.", "suggested_assignee_role": "security_lead"},
            {"order": 5, "title": "Draft internal & external comms", "description": "Use AI Comm Drafter to produce stakeholder + customer messages.", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Customer notification", "description": "Send breach notifications per jurisdiction.", "suggested_assignee_role": "comms_lead"},
            {"order": 7, "title": "Post-incident review", "description": "Run blameless retrospective within 7 days.", "suggested_assignee_role": "engineering_lead"},
        ],
    },
    {
        "name": "Production Outage",
        "category": "operational",
        "description": "Major customer-facing service outage (P0/P1).",
        "steps": [
            {"order": 1, "title": "Page on-call & open incident channel", "suggested_assignee_role": "on_call_engineer"},
            {"order": 2, "title": "Establish IC (Incident Commander) and Comms lead", "suggested_assignee_role": "engineering_lead"},
            {"order": 3, "title": "Post first status page update within 15 minutes", "suggested_assignee_role": "comms_lead"},
            {"order": 4, "title": "Identify root cause hypothesis", "suggested_assignee_role": "on_call_engineer"},
            {"order": 5, "title": "Mitigate (rollback / failover / capacity)", "suggested_assignee_role": "on_call_engineer"},
            {"order": 6, "title": "Customer comms cadence (every 30 min)", "suggested_assignee_role": "comms_lead"},
            {"order": 7, "title": "Confirm resolution and update status page", "suggested_assignee_role": "engineering_lead"},
            {"order": 8, "title": "Schedule post-mortem within 5 business days", "suggested_assignee_role": "engineering_lead"},
        ],
    },
    {
        "name": "Executive Issue / Leadership Crisis",
        "category": "hr",
        "description": "Allegations or conduct issues involving an executive or board member.",
        "steps": [
            {"order": 1, "title": "Convene crisis committee (CEO, GC, CHRO, Board liaison)", "suggested_assignee_role": "ceo"},
            {"order": 2, "title": "Preserve evidence & engage outside counsel", "suggested_assignee_role": "general_counsel"},
            {"order": 3, "title": "Determine interim governance / leadership coverage", "suggested_assignee_role": "ceo"},
            {"order": 4, "title": "Draft holding statement (no admission)", "suggested_assignee_role": "comms_lead"},
            {"order": 5, "title": "Notify board / major investors", "suggested_assignee_role": "ceo"},
            {"order": 6, "title": "Decide investigation scope & external firm", "suggested_assignee_role": "general_counsel"},
            {"order": 7, "title": "Internal all-hands message", "suggested_assignee_role": "ceo"},
        ],
    },
    {
        "name": "Public Relations Crisis",
        "category": "pr",
        "description": "Viral negative media / social coverage threatening brand reputation.",
        "steps": [
            {"order": 1, "title": "Pause all scheduled marketing / social content", "suggested_assignee_role": "marketing_lead"},
            {"order": 2, "title": "Stand up monitoring (media, social, sentiment)", "suggested_assignee_role": "comms_lead"},
            {"order": 3, "title": "Decide tone: defend, acknowledge, or stay silent", "suggested_assignee_role": "ceo"},
            {"order": 4, "title": "Draft official response with legal review", "suggested_assignee_role": "comms_lead"},
            {"order": 5, "title": "Brief customer-facing teams (support, sales)", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Issue public statement on owned channels", "suggested_assignee_role": "comms_lead"},
            {"order": 7, "title": "Track sentiment trajectory and adjust", "suggested_assignee_role": "comms_lead"},
        ],
    },
    {
        "name": "Safety / Physical Incident",
        "category": "operational",
        "description": "Workplace injury, evacuation, or other physical-safety event.",
        "steps": [
            {"order": 1, "title": "Ensure people are safe & call emergency services", "suggested_assignee_role": "facilities_lead"},
            {"order": 2, "title": "Account for all personnel", "suggested_assignee_role": "facilities_lead"},
            {"order": 3, "title": "Notify HR & EHS officer", "suggested_assignee_role": "hr_lead"},
            {"order": 4, "title": "Preserve scene for investigation", "suggested_assignee_role": "facilities_lead"},
            {"order": 5, "title": "Report to regulators (OSHA etc.) if required", "suggested_assignee_role": "general_counsel"},
            {"order": 6, "title": "Internal communication & support resources", "suggested_assignee_role": "hr_lead"},
            {"order": 7, "title": "Root-cause investigation & corrective actions", "suggested_assignee_role": "facilities_lead"},
        ],
    },
]


async def seed_playbooks(db: AsyncSession) -> dict[str, int]:
    """Insert any missing seed playbooks. Returns counts of {created, skipped}."""
    created = 0
    skipped = 0
    for template in SEED_TEMPLATES:
        stmt = select(Playbook).where(Playbook.name == template["name"])
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue
        pb = Playbook(**template)
        db.add(pb)
        created += 1
    if created:
        await db.commit()
    return {"created": created, "skipped": skipped}
