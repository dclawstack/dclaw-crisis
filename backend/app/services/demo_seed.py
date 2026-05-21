"""Seed and reset a realistic demo dataset.

Every demo row is identifiable by an unambiguous marker:
- Crisis.title         "DEMO: "
- TeamMember.name      "DEMO: "
- Stakeholder.name     "DEMO: "
- Resource.name        "DEMO: "
- Simulation.name      "DEMO: "
- LegalHold.title      "DEMO: "
- Signal.source        "demo:"
- MediaMention.outlet  "DEMO "
- User.email           settings.demo_user_email (single known address)

`reset_demo` deletes ONLY rows matching these markers — real operator data is
never touched. ActionItems, Communications, and ContinuityActivations cascade
from Crisis, so they go too.
"""
from __future__ import annotations

from datetime import timedelta

import bcrypt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import utc_now
from app.models.action_item import ActionItem
from app.models.communication import Communication
from app.models.crisis import Crisis
from app.models.legal_hold import LegalHold, LegalHoldStatus
from app.models.media_mention import MediaMention, MentionSentiment
from app.models.resource import Resource
from app.models.signal import Signal, SignalStatus
from app.models.simulation import Simulation, SimulationStatus
from app.models.stakeholder import Stakeholder
from app.models.team_member import TeamMember
from app.models.user import User

CRISIS_PREFIX = "DEMO: "
TEAM_PREFIX = "DEMO: "
STAKEHOLDER_PREFIX = "DEMO: "
RESOURCE_PREFIX = "DEMO: "
SIMULATION_PREFIX = "DEMO: "
LEGAL_PREFIX = "DEMO: "
SIGNAL_SOURCE_PREFIX = "demo:"
MEDIA_OUTLET_PREFIX = "DEMO "


def demo_credentials() -> dict[str, str]:
    """Public credentials a landing-page visitor uses to sign in as the demo user."""
    return {"email": settings.demo_user_email, "password": settings.demo_user_password}


async def get_demo_counts(db: AsyncSession) -> dict[str, int]:
    """Return how many demo rows exist per entity type."""
    counts: dict[str, int] = {}

    async def _count(stmt) -> int:
        rows = (await db.execute(stmt)).scalars().all()
        return len(list(rows))

    counts["crises"] = await _count(select(Crisis).where(Crisis.title.startswith(CRISIS_PREFIX)))
    counts["team_members"] = await _count(select(TeamMember).where(TeamMember.name.startswith(TEAM_PREFIX)))
    counts["stakeholders"] = await _count(select(Stakeholder).where(Stakeholder.name.startswith(STAKEHOLDER_PREFIX)))
    counts["resources"] = await _count(select(Resource).where(Resource.name.startswith(RESOURCE_PREFIX)))
    counts["signals"] = await _count(select(Signal).where(Signal.source.startswith(SIGNAL_SOURCE_PREFIX)))
    counts["simulations"] = await _count(select(Simulation).where(Simulation.name.startswith(SIMULATION_PREFIX)))
    counts["legal_holds"] = await _count(select(LegalHold).where(LegalHold.title.startswith(LEGAL_PREFIX)))
    counts["media_mentions"] = await _count(select(MediaMention).where(MediaMention.outlet.startswith(MEDIA_OUTLET_PREFIX)))
    return counts


async def is_seeded(db: AsyncSession) -> bool:
    counts = await get_demo_counts(db)
    return any(v > 0 for v in counts.values())


async def seed_demo(db: AsyncSession) -> dict[str, int]:
    """Insert a realistic demo dataset + create the demo user.

    Idempotent — re-running returns the existing counts and the same
    credentials so the frontend can keep showing the sign-in panel.
    """
    if await is_seeded(db):
        return {"created": 0, "skipped": "already-seeded", **await get_demo_counts(db)}

    now = utc_now()

    # ── Demo user (so a landing-page visitor can sign in without signup) ──
    existing_user = (await db.execute(
        select(User).where(User.email == settings.demo_user_email)
    )).scalar_one_or_none()
    if existing_user is None:
        password_hash = bcrypt.hashpw(
            settings.demo_user_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("ascii")
        db.add(User(
            email=settings.demo_user_email,
            name=settings.demo_user_name,
            password_hash=password_hash,
            auth_provider="local",
            is_active=True,
            is_admin=False,
        ))
        await db.flush()

    # ── Team members ─────────────────────────────────────────────────
    incident_commander = TeamMember(
        name=f"{TEAM_PREFIX}Maya Kowalski",
        email="demo-ic@dclaw-crisis.example",
        role="Incident Commander",
        department="Engineering",
        is_active=True,
    )
    security_lead = TeamMember(
        name=f"{TEAM_PREFIX}Jordan Chen",
        email="demo-sec@dclaw-crisis.example",
        role="Security Lead",
        department="Security",
        is_active=True,
    )
    comms_lead = TeamMember(
        name=f"{TEAM_PREFIX}Priya Patel",
        email="demo-comms@dclaw-crisis.example",
        role="Comms Lead",
        department="Communications",
        is_active=True,
    )
    db.add_all([incident_commander, security_lead, comms_lead])
    await db.flush()

    # ── Stakeholders ─────────────────────────────────────────────────
    db.add_all([
        Stakeholder(
            name=f"{STAKEHOLDER_PREFIX}Acme Corp Procurement",
            type="customer", organization="Acme Corp", importance="critical",
            email="ops@acme.example", tags=["enterprise", "renewal-q3"], is_active=True,
        ),
        Stakeholder(
            name=f"{STAKEHOLDER_PREFIX}FTC Office",
            type="regulator", organization="Federal Trade Commission", importance="critical",
            email="reports@ftc.example", is_active=True,
        ),
        Stakeholder(
            name=f"{STAKEHOLDER_PREFIX}TechCrunch Reporter",
            type="media", organization="TechCrunch", importance="medium",
            email="tips@techcrunch.example", is_active=True,
        ),
        Stakeholder(
            name=f"{STAKEHOLDER_PREFIX}Board Audit Committee",
            type="board", importance="high", is_active=True,
        ),
        Stakeholder(
            name=f"{STAKEHOLDER_PREFIX}Marketing Team All-Hands",
            type="internal", importance="low", tags=["pr", "internal"], is_active=True,
        ),
    ])

    # ── Resources ────────────────────────────────────────────────────
    db.add_all([
        Resource(
            name=f"{RESOURCE_PREFIX}Boston War Room A",
            resource_type="war_room", status="available", capacity="12 people",
            location="HQ, floor 4", attributes={"av": True, "secure_line": True},
        ),
        Resource(
            name=f"{RESOURCE_PREFIX}#incidents Slack channel",
            resource_type="comm_channel", status="available",
            attributes={"platform": "slack", "members": 50},
        ),
        Resource(
            name=f"{RESOURCE_PREFIX}CrowdStrike IR retainer",
            resource_type="vendor_contact", status="available", capacity="24/7 on-call",
        ),
        Resource(
            name=f"{RESOURCE_PREFIX}Outside Counsel — Lewis Brisbois",
            resource_type="vendor_contact", status="in_use",
            notes="Engaged on Q2 incident",
        ),
        Resource(
            name=f"{RESOURCE_PREFIX}On-call roster — eng",
            resource_type="on_call_roster", status="available",
        ),
        Resource(
            name=f"{RESOURCE_PREFIX}Crisis budget pool",
            resource_type="budget_pool", status="available", capacity="$250K Q3",
        ),
    ])

    # ── Active crisis (responding) ───────────────────────────────────
    active_crisis = Crisis(
        title=f"{CRISIS_PREFIX}Payments API outage — Stripe webhook failure",
        description=(
            "Stripe webhooks failing since 13:00 UTC; approximately 40% of checkout transactions "
            "are returning errors. Suspected misconfiguration in the webhook retry policy after "
            "yesterday's release."
        ),
        severity="high",
        status="responding",
        category="operational",
        detected_at=now - timedelta(hours=2),
        estimated_impact_usd=85000.0,
        lead_id=incident_commander.id,
    )
    db.add(active_crisis)
    await db.flush()

    db.add_all([
        ActionItem(
            crisis_id=active_crisis.id, title="Engage Stripe support — open P1 ticket",
            description="Open priority ticket with Stripe and request immediate engineering bridge.",
            assignee_id=incident_commander.id, status="completed", priority="critical",
            completed_at=now - timedelta(hours=1, minutes=30),
        ),
        ActionItem(
            crisis_id=active_crisis.id, title="Roll back yesterday's webhook handler deploy",
            description="Revert to last-known-good build and re-deploy.",
            assignee_id=incident_commander.id, status="in_progress", priority="critical",
            due_at=now + timedelta(minutes=30),
        ),
        ActionItem(
            crisis_id=active_crisis.id, title="Notify top 10 enterprise customers proactively",
            description="Customer success team to call critical accounts before they call us.",
            assignee_id=comms_lead.id, status="in_progress", priority="high",
        ),
        ActionItem(
            crisis_id=active_crisis.id, title="Status page update with ETA",
            description="Public status page acknowledging the issue and committing to next update window.",
            assignee_id=comms_lead.id, status="completed", priority="high",
            completed_at=now - timedelta(hours=1),
        ),
        ActionItem(
            crisis_id=active_crisis.id, title="Audit affected transactions, prepare reconciliation",
            description="Identify failed transactions and prepare retry/refund batch.",
            assignee_id=security_lead.id, status="pending", priority="medium",
        ),
        ActionItem(
            crisis_id=active_crisis.id, title="Internal status standup every 30 min",
            description="Rolling internal updates until contained.",
            assignee_id=incident_commander.id, status="blocked", priority="medium",
        ),
    ])
    db.add_all([
        Communication(
            crisis_id=active_crisis.id, author_id=comms_lead.id,
            message=(
                "[DEMO] We are aware of an issue affecting checkout payments. Our engineering team "
                "is actively investigating. Next update by 14:30 UTC."
            ),
            comm_type="stakeholder_alert", channel="email",
            delivery_status="sent", sent_at=now - timedelta(hours=1),
            delivery_log={"provider": "simulator:email", "status": "sent"},
            sentiment="neutral", sentiment_score=0.05,
            sentiment_analyzed_at=now - timedelta(minutes=50),
            predicted_reaction="Customers will appreciate the acknowledgement but expect specifics in the next update.",
            risk_flags=["no impact scope quantified", "no workaround offered"],
        ),
        Communication(
            crisis_id=active_crisis.id, author_id=incident_commander.id,
            message="[DEMO] Internal: All hands engaged. IC: Maya. Bridge: war room A. Comms cadence 30 min.",
            comm_type="internal_update", channel="slack",
            delivery_status="sent", sent_at=now - timedelta(hours=1, minutes=45),
            delivery_log={"provider": "simulator:slack", "status": "sent"},
        ),
    ])

    # ── Resolved crisis ──────────────────────────────────────────────
    resolved_crisis = Crisis(
        title=f"{CRISIS_PREFIX}Q2 PR incident — viral support thread",
        description=(
            "A customer support thread on social media gained traction after a perceived "
            "tone-deaf response. Brand sentiment dipped for 36 hours before recovery."
        ),
        severity="medium",
        status="resolved",
        category="pr",
        detected_at=now - timedelta(days=42),
        resolved_at=now - timedelta(days=40),
        estimated_impact_usd=15000.0,
        lead_id=comms_lead.id,
    )
    db.add(resolved_crisis)
    await db.flush()

    db.add_all([
        ActionItem(
            crisis_id=resolved_crisis.id, title="Issue corrected public statement",
            assignee_id=comms_lead.id, status="completed", priority="critical",
            completed_at=now - timedelta(days=41, hours=12),
        ),
        ActionItem(
            crisis_id=resolved_crisis.id, title="Direct outreach to the originating customer",
            assignee_id=comms_lead.id, status="completed", priority="high",
            completed_at=now - timedelta(days=41, hours=8),
        ),
        ActionItem(
            crisis_id=resolved_crisis.id, title="Update support response playbook",
            assignee_id=incident_commander.id, status="completed", priority="medium",
            completed_at=now - timedelta(days=40, hours=2),
        ),
        ActionItem(
            crisis_id=resolved_crisis.id, title="Brief team on lessons learned",
            assignee_id=incident_commander.id, status="completed", priority="low",
            completed_at=now - timedelta(days=39),
        ),
    ])

    # ── Signals ──────────────────────────────────────────────────────
    db.add_all([
        Signal(
            source=f"{SIGNAL_SOURCE_PREFIX}webhook:datadog",
            source_url="https://datadog.example/alert/12345",
            raw_text=(
                "HTTP 5xx rate on payments-api exceeded 40% over the last 5 minutes across "
                "us-east-1 and eu-west-1. Synthetic checks failing on /checkout."
            ),
            ai_summary="Payments API returning 40% 5xx errors across two regions; checkout failing.",
            ai_severity="critical", ai_category="operational", ai_confidence=0.92,
            ai_rationale="Sustained, multi-region, customer-facing impact.",
            ai_recommends_promotion=True,
            status=SignalStatus.promoted,
            crisis_id=active_crisis.id,
            detected_at=now - timedelta(hours=2, minutes=5),
        ),
        Signal(
            source=f"{SIGNAL_SOURCE_PREFIX}rss:hacker-news",
            source_url="https://news.ycombinator.example/item?id=42",
            raw_text="Discussion thread: 'Anyone else seeing checkout failures right now?'",
            ai_summary="Public discussion thread referencing checkout failures.",
            ai_severity="medium", ai_category="pr", ai_confidence=0.65,
            ai_recommends_promotion=False,
            status=SignalStatus.triaged,
            detected_at=now - timedelta(hours=1, minutes=15),
        ),
        Signal(
            source=f"{SIGNAL_SOURCE_PREFIX}rss:company-blog",
            raw_text="Read our new whitepaper on the future of remote work — out now on our blog!",
            ai_summary="Marketing announcement; not a crisis signal.",
            ai_severity="low", ai_category="other", ai_confidence=0.95,
            ai_recommends_promotion=False,
            status=SignalStatus.dismissed,
            detected_at=now - timedelta(hours=4),
        ),
    ])

    # ── Simulation ───────────────────────────────────────────────────
    db.add(Simulation(
        name=f"{SIMULATION_PREFIX}Q3 Tabletop — ransomware drill",
        scenario_type="security", severity="critical",
        generated_scenario=(
            "08:23 EST: SOC analyst receives multiple alerts from Splunk for abnormal file encryption "
            "activity on core-banking-prod-01. CrowdStrike alerts show 'Ransomware Behavior Detected'.\n\n"
            "— At T+30 minutes: Press inquiry from TechCrunch."
        ),
        generated_actions=[
            {"order": 1, "action": "Isolate affected hosts", "role": "security_lead"},
            {"order": 2, "action": "Engage IR retainer + cyber insurance", "role": "general_counsel"},
            {"order": 3, "action": "Preserve forensic evidence", "role": "forensics"},
            {"order": 4, "action": "Decide on ransom policy with legal+leadership", "role": "ceo"},
        ],
        expected_outcomes=[
            "Containment within 60 minutes",
            "Legal counsel engaged within 90 minutes",
            "Backup integrity verified before any recovery",
            "Coordinated comms — internal and customer-facing",
        ],
        operator_notes=(
            "Containment achieved at T+55 min. Legal engaged at T+45 min. Backup test added to runbook. "
            "Comms went out on time but tone was too defensive."
        ),
        evaluation_summary="Strong technical response. Comms tone needs work — see breakdown.",
        score=0.78,
        evaluation_breakdown=[
            {"expected_outcome": "Containment within 60 minutes", "achieved": "yes", "comment": "T+55 min."},
            {"expected_outcome": "Legal counsel engaged within 90 minutes", "achieved": "yes", "comment": "T+45 min."},
            {"expected_outcome": "Backup integrity verified before any recovery", "achieved": "yes", "comment": "Test pre-restore."},
            {"expected_outcome": "Coordinated comms — internal and customer-facing", "achieved": "partial", "comment": "Tone too defensive in customer comms; rewrite needed."},
        ],
        status=SimulationStatus.completed,
        started_at=now - timedelta(days=14, hours=2),
        completed_at=now - timedelta(days=14),
    ))

    # ── Legal hold ───────────────────────────────────────────────────
    db.add(LegalHold(
        crisis_id=resolved_crisis.id,
        title=f"{LEGAL_PREFIX}Q2 PR incident — preservation matter",
        scope_description=(
            "Preserve all internal communications and public-facing posts related to the "
            "Q2 PR incident from 30 days before through 60 days after the originating support thread."
        ),
        custodians=[
            {"name": "Maya Kowalski", "email": "maya@dclaw-crisis.example", "role": "IC"},
            {"name": "Priya Patel", "email": "priya@dclaw-crisis.example", "role": "Comms"},
        ],
        data_sources=["M365 email", "Slack", "Zendesk", "Twitter/X account exports"],
        hold_notice_text=(
            "[AI-GENERATED DRAFT — NOT LEGAL ADVICE. Have outside counsel review before issuing.]\n\n"
            "MATTER: Q2 Customer Support Communications\n\n"
            "You are hereby notified that the organization is preserving documents and communications "
            "related to the Q2 customer support incident. Do not delete, modify, or move any related "
            "emails, Slack messages, support tickets, or social media drafts during the hold period."
        ),
        issued_by="general_counsel",
        status=LegalHoldStatus.active,
        issued_at=now - timedelta(days=41),
    ))

    # ── Media mentions ───────────────────────────────────────────────
    db.add_all([
        MediaMention(
            outlet=f"{MEDIA_OUTLET_PREFIX}TechCrunch",
            url="https://techcrunch.example/2026/payments-outage",
            headline="Payments service outage hits major SaaS provider's customers",
            snippet=(
                "Several enterprise customers reported checkout failures starting around 1pm UTC. "
                "The company acknowledged the issue on its status page and committed to updates every 30 minutes."
            ),
            author="Demo Reporter",
            sentiment=MentionSentiment.negative,
            sentiment_score=-0.45,
            key_themes=["customer impact", "transparency", "operational reliability"],
            analyzed_at=now - timedelta(hours=1),
            crisis_id=active_crisis.id,
            mentioned_at=now - timedelta(hours=1, minutes=30),
        ),
        MediaMention(
            outlet=f"{MEDIA_OUTLET_PREFIX}Reuters",
            headline="Analysts praise rapid response to payments incident",
            snippet=(
                "Industry analysts noted the company's measured response and clear customer "
                "communication contrasts favorably with prior industry incidents."
            ),
            sentiment=MentionSentiment.positive,
            sentiment_score=0.55,
            key_themes=["rapid response", "transparent communication"],
            analyzed_at=now - timedelta(minutes=20),
            crisis_id=active_crisis.id,
            mentioned_at=now - timedelta(minutes=30),
        ),
    ])

    await db.commit()
    counts = await get_demo_counts(db)
    return {"created": sum(counts.values()), "skipped": 0, **counts}


async def reset_demo(db: AsyncSession) -> dict[str, int]:
    """Remove every demo row INCLUDING the demo user. Real (non-prefixed) data is untouched.

    Order: child tables first if cascade isn't enough, then crises so the
    ActionItem/Communication/ContinuityActivation cascades fire. Demo user is
    deleted last — keyed by `settings.demo_user_email`, so only that single
    address is touched.
    """
    deleted: dict[str, int] = {}

    # Anything that doesn't cascade from Crisis — must be deleted explicitly.
    deleted["signals"] = await _delete_where_prefix(db, Signal, "source", SIGNAL_SOURCE_PREFIX)
    deleted["media_mentions"] = await _delete_where_prefix(db, MediaMention, "outlet", MEDIA_OUTLET_PREFIX)
    deleted["legal_holds"] = await _delete_where_prefix(db, LegalHold, "title", LEGAL_PREFIX)
    deleted["simulations"] = await _delete_where_prefix(db, Simulation, "name", SIMULATION_PREFIX)

    # Crises cascade-delete their action items + comms + continuity activations.
    deleted["crises"] = await _delete_where_prefix(db, Crisis, "title", CRISIS_PREFIX)

    deleted["stakeholders"] = await _delete_where_prefix(db, Stakeholder, "name", STAKEHOLDER_PREFIX)
    deleted["resources"] = await _delete_where_prefix(db, Resource, "name", RESOURCE_PREFIX)
    deleted["team_members"] = await _delete_where_prefix(db, TeamMember, "name", TEAM_PREFIX)

    # Demo user — keyed on the exact email so we can never collateral-delete anyone else.
    user_res = await db.execute(delete(User).where(User.email == settings.demo_user_email))
    deleted["users"] = user_res.rowcount or 0

    await db.commit()
    deleted["total"] = sum(deleted.values())
    return deleted


# Backward-compatible alias for any external caller still using the old name.
clear_demo = reset_demo


async def _delete_where_prefix(db: AsyncSession, model, field_name: str, prefix: str) -> int:
    field = getattr(model, field_name)
    res = await db.execute(delete(model).where(field.startswith(prefix)))
    return res.rowcount or 0
