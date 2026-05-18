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
    {
        "name": "Ransomware / Active Encryption Event",
        "category": "security",
        "description": "Active ransomware encryption detected on internal systems.",
        "steps": [
            {"order": 1, "title": "Isolate affected hosts & sever network segments", "suggested_assignee_role": "security_lead"},
            {"order": 2, "title": "DO NOT power off — preserve volatile memory for forensics", "suggested_assignee_role": "forensics"},
            {"order": 3, "title": "Engage IR retainer + cyber insurance carrier", "suggested_assignee_role": "general_counsel"},
            {"order": 4, "title": "Identify ransomware family and check for decryptor", "suggested_assignee_role": "security_lead"},
            {"order": 5, "title": "Inventory affected data & determine notification obligations", "suggested_assignee_role": "general_counsel"},
            {"order": 6, "title": "Restore from clean backups (validate integrity first)", "suggested_assignee_role": "engineering_lead"},
            {"order": 7, "title": "Decide on ransom payment policy with legal + leadership (do NOT pay without counsel)", "suggested_assignee_role": "ceo"},
            {"order": 8, "title": "Coordinated customer & employee communications", "suggested_assignee_role": "comms_lead"},
        ],
    },
    {
        "name": "Major Cloud Provider Outage",
        "category": "operational",
        "description": "AWS / GCP / Azure region-wide failure affecting our services.",
        "steps": [
            {"order": 1, "title": "Confirm scope via provider status page + independent monitors", "suggested_assignee_role": "on_call_engineer"},
            {"order": 2, "title": "Activate cross-region/cross-cloud failover if available", "suggested_assignee_role": "on_call_engineer"},
            {"order": 3, "title": "Throttle non-essential traffic & background jobs", "suggested_assignee_role": "on_call_engineer"},
            {"order": 4, "title": "Status page update — acknowledge dependency", "suggested_assignee_role": "comms_lead"},
            {"order": 5, "title": "Direct enterprise customer outreach if SLA at risk", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Track restore + reconcile data written during failover", "suggested_assignee_role": "engineering_lead"},
            {"order": 7, "title": "Post-incident review with cloud architecture team", "suggested_assignee_role": "engineering_lead"},
        ],
    },
    {
        "name": "Key Personnel Sudden Departure",
        "category": "hr",
        "description": "Critical role-holder leaves without notice (death, illness, sudden resignation).",
        "steps": [
            {"order": 1, "title": "Convene executive team & legal to confirm circumstances", "suggested_assignee_role": "ceo"},
            {"order": 2, "title": "Lock access credentials and rotate shared secrets", "suggested_assignee_role": "security_lead"},
            {"order": 3, "title": "Identify interim coverage & decision authority", "suggested_assignee_role": "ceo"},
            {"order": 4, "title": "Notify direct reports and team in coordinated waves", "suggested_assignee_role": "hr_lead"},
            {"order": 5, "title": "Document in-flight work and pending decisions", "suggested_assignee_role": "engineering_lead"},
            {"order": 6, "title": "External communications if customer-facing or public", "suggested_assignee_role": "comms_lead"},
            {"order": 7, "title": "Begin permanent replacement search", "suggested_assignee_role": "hr_lead"},
        ],
    },
    {
        "name": "Regulatory Inquiry / Investigation",
        "category": "legal",
        "description": "Government regulator opens formal inquiry or investigation.",
        "steps": [
            {"order": 1, "title": "Engage outside counsel with relevant expertise", "suggested_assignee_role": "general_counsel"},
            {"order": 2, "title": "Issue litigation hold — preserve all relevant documents", "suggested_assignee_role": "general_counsel"},
            {"order": 3, "title": "Identify scope: which jurisdictions, statutes, time periods", "suggested_assignee_role": "general_counsel"},
            {"order": 4, "title": "Designate single point of contact for regulator", "suggested_assignee_role": "general_counsel"},
            {"order": 5, "title": "Brief board + audit committee", "suggested_assignee_role": "ceo"},
            {"order": 6, "title": "Disclosure analysis (SEC filings, insurance carriers)", "suggested_assignee_role": "general_counsel"},
            {"order": 7, "title": "Internal communications guidance — no speculation, route media to PR", "suggested_assignee_role": "comms_lead"},
        ],
    },
    {
        "name": "Product Safety Recall",
        "category": "operational",
        "description": "Defect requiring recall, repair, or replacement of shipped product.",
        "steps": [
            {"order": 1, "title": "Confirm defect with engineering + QA", "suggested_assignee_role": "engineering_lead"},
            {"order": 2, "title": "Halt shipments & quarantine inventory", "suggested_assignee_role": "operations_lead"},
            {"order": 3, "title": "Determine recall classification & regulator notification (CPSC, FDA, etc.)", "suggested_assignee_role": "general_counsel"},
            {"order": 4, "title": "Identify affected serial/lot numbers and impacted customers", "suggested_assignee_role": "operations_lead"},
            {"order": 5, "title": "Customer notification plan + return logistics", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Public statement + dedicated recall webpage", "suggested_assignee_role": "comms_lead"},
            {"order": 7, "title": "Reconcile financial impact with finance & insurance", "suggested_assignee_role": "cfo"},
        ],
    },
    {
        "name": "GDPR / CCPA Data Subject Request",
        "category": "legal",
        "description": "Complex DSAR or right-to-be-forgotten request with risk of non-compliance.",
        "steps": [
            {"order": 1, "title": "Verify requester identity per privacy policy", "suggested_assignee_role": "privacy_officer"},
            {"order": 2, "title": "Locate all personal data across systems + vendors", "suggested_assignee_role": "engineering_lead"},
            {"order": 3, "title": "Assess deletion exemptions (litigation hold, regulatory retention)", "suggested_assignee_role": "general_counsel"},
            {"order": 4, "title": "Execute deletion/export within statutory deadline (30 days GDPR, 45 days CCPA)", "suggested_assignee_role": "privacy_officer"},
            {"order": 5, "title": "Notify downstream processors & vendors", "suggested_assignee_role": "privacy_officer"},
            {"order": 6, "title": "Document compliance trail for audit", "suggested_assignee_role": "privacy_officer"},
        ],
    },
    {
        "name": "Third-Party Vendor Failure",
        "category": "supply_chain",
        "description": "Critical SaaS / API vendor goes down, breaches their SLA, or announces shutdown.",
        "steps": [
            {"order": 1, "title": "Confirm scope of vendor failure & expected duration", "suggested_assignee_role": "engineering_lead"},
            {"order": 2, "title": "Activate fallback or degraded mode for our service", "suggested_assignee_role": "on_call_engineer"},
            {"order": 3, "title": "Review vendor contract for SLA credits + termination clauses", "suggested_assignee_role": "general_counsel"},
            {"order": 4, "title": "Customer impact assessment & communication plan", "suggested_assignee_role": "comms_lead"},
            {"order": 5, "title": "Evaluate alternate vendors & migration cost", "suggested_assignee_role": "procurement_lead"},
            {"order": 6, "title": "Post-incident: revisit single-vendor dependencies", "suggested_assignee_role": "engineering_lead"},
        ],
    },
    {
        "name": "DDoS / Volumetric Attack",
        "category": "security",
        "description": "Large-scale denial-of-service attack against our infrastructure.",
        "steps": [
            {"order": 1, "title": "Confirm attack pattern with network monitoring", "suggested_assignee_role": "security_lead"},
            {"order": 2, "title": "Enable upstream DDoS mitigation (Cloudflare/Akamai)", "suggested_assignee_role": "security_lead"},
            {"order": 3, "title": "Block attacker source ranges & geo-fence if appropriate", "suggested_assignee_role": "security_lead"},
            {"order": 4, "title": "Status page update + customer communication", "suggested_assignee_role": "comms_lead"},
            {"order": 5, "title": "Engage law enforcement if extortion is involved", "suggested_assignee_role": "general_counsel"},
            {"order": 6, "title": "Capture forensic data + report to ISP", "suggested_assignee_role": "security_lead"},
            {"order": 7, "title": "Post-mortem on capacity headroom + mitigation gaps", "suggested_assignee_role": "engineering_lead"},
        ],
    },
    {
        "name": "Phishing / Business Email Compromise",
        "category": "security",
        "description": "Successful phishing campaign or BEC affecting employees or finance.",
        "steps": [
            {"order": 1, "title": "Lock affected accounts & force password reset", "suggested_assignee_role": "security_lead"},
            {"order": 2, "title": "Revoke session tokens + rotate API keys", "suggested_assignee_role": "security_lead"},
            {"order": 3, "title": "If financial transfer occurred: contact bank + FBI IC3 within 24h", "suggested_assignee_role": "cfo"},
            {"order": 4, "title": "Email gateway scan for similar messages — quarantine", "suggested_assignee_role": "security_lead"},
            {"order": 5, "title": "All-staff warning with phishing indicators (no blame)", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Audit downstream system access during compromise window", "suggested_assignee_role": "security_lead"},
            {"order": 7, "title": "Phishing-resistant MFA rollout where missing", "suggested_assignee_role": "security_lead"},
        ],
    },
    {
        "name": "Financial Fraud / Embezzlement",
        "category": "financial",
        "description": "Suspected internal financial fraud, expense fraud, or embezzlement.",
        "steps": [
            {"order": 1, "title": "Restrict access of suspected individual without alerting (avoid evidence destruction)", "suggested_assignee_role": "security_lead"},
            {"order": 2, "title": "Preserve financial records + email evidence", "suggested_assignee_role": "general_counsel"},
            {"order": 3, "title": "Engage forensic accountants", "suggested_assignee_role": "cfo"},
            {"order": 4, "title": "Notify audit committee & board chair confidentially", "suggested_assignee_role": "cfo"},
            {"order": 5, "title": "Decide on law enforcement referral + insurance claim", "suggested_assignee_role": "general_counsel"},
            {"order": 6, "title": "Employment action with HR + counsel", "suggested_assignee_role": "hr_lead"},
            {"order": 7, "title": "Disclosure analysis (auditors, lenders, investors)", "suggested_assignee_role": "cfo"},
        ],
    },
    {
        "name": "IP Theft / Trade Secret Leak",
        "category": "legal",
        "description": "Confirmed or suspected exfiltration of source code, customer lists, or trade secrets.",
        "steps": [
            {"order": 1, "title": "Preserve all evidence (host images, badge logs, email)", "suggested_assignee_role": "forensics"},
            {"order": 2, "title": "Engage outside counsel + send preservation letter to suspected party", "suggested_assignee_role": "general_counsel"},
            {"order": 3, "title": "Rotate keys + audit external access to repos and data warehouses", "suggested_assignee_role": "security_lead"},
            {"order": 4, "title": "Assess competitive impact — what could the recipient do with this?", "suggested_assignee_role": "ceo"},
            {"order": 5, "title": "Decide on injunction / DTSA filing", "suggested_assignee_role": "general_counsel"},
            {"order": 6, "title": "Internal review of confidentiality controls", "suggested_assignee_role": "security_lead"},
        ],
    },
    {
        "name": "Executive Impersonation / Deepfake",
        "category": "pr",
        "description": "Fake video, audio, or social-media account impersonating an executive.",
        "steps": [
            {"order": 1, "title": "Verify the impersonation is not real (with executive directly)", "suggested_assignee_role": "ceo"},
            {"order": 2, "title": "Document the artifact (capture, hash, timestamp) before takedown", "suggested_assignee_role": "security_lead"},
            {"order": 3, "title": "File platform takedown requests (Twitter/X, LinkedIn, Meta, YouTube)", "suggested_assignee_role": "comms_lead"},
            {"order": 4, "title": "Public statement on owned channels disclaiming the artifact", "suggested_assignee_role": "comms_lead"},
            {"order": 5, "title": "Warn employees, customers, and partners — risk of follow-on scam", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Engage law enforcement + legal counsel for civil/criminal options", "suggested_assignee_role": "general_counsel"},
        ],
    },
    {
        "name": "Insider Threat",
        "category": "security",
        "description": "Employee or contractor maliciously or negligently risking the organization.",
        "steps": [
            {"order": 1, "title": "Document evidence with HR + Legal before any access changes", "suggested_assignee_role": "general_counsel"},
            {"order": 2, "title": "Revoke access in a controlled window (avoid tipping off if criminal)", "suggested_assignee_role": "security_lead"},
            {"order": 3, "title": "Forensic review of activity logs", "suggested_assignee_role": "forensics"},
            {"order": 4, "title": "Determine criminal vs. employment-only response", "suggested_assignee_role": "general_counsel"},
            {"order": 5, "title": "Coordinated termination + escort if needed", "suggested_assignee_role": "hr_lead"},
            {"order": 6, "title": "Notify affected customers if data exposure occurred", "suggested_assignee_role": "comms_lead"},
            {"order": 7, "title": "Review detective controls + privilege model", "suggested_assignee_role": "security_lead"},
        ],
    },
    {
        "name": "Natural Disaster / Site Loss",
        "category": "operational",
        "description": "Fire, flood, earthquake, or other disaster destroying or disabling a key site.",
        "steps": [
            {"order": 1, "title": "Confirm all personnel safe & accounted for", "suggested_assignee_role": "facilities_lead"},
            {"order": 2, "title": "Activate BCP / DR plan for affected location", "suggested_assignee_role": "operations_lead"},
            {"order": 3, "title": "Notify insurance carrier & document damage", "suggested_assignee_role": "cfo"},
            {"order": 4, "title": "Stand up alternate work locations / remote work", "suggested_assignee_role": "facilities_lead"},
            {"order": 5, "title": "Customer + supplier communications on continuity", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Employee assistance (housing, pay continuity, mental health)", "suggested_assignee_role": "hr_lead"},
            {"order": 7, "title": "Site restoration or relocation plan", "suggested_assignee_role": "facilities_lead"},
        ],
    },
    {
        "name": "Pandemic / Public Health Emergency",
        "category": "operational",
        "description": "Outbreak or public-health emergency affecting workforce and operations.",
        "steps": [
            {"order": 1, "title": "Establish a cross-functional response committee", "suggested_assignee_role": "ceo"},
            {"order": 2, "title": "Source authoritative guidance (CDC/WHO/local health authority)", "suggested_assignee_role": "hr_lead"},
            {"order": 3, "title": "Update remote-work, travel, and quarantine policies", "suggested_assignee_role": "hr_lead"},
            {"order": 4, "title": "Site-level safety protocols (cleaning, screening, distancing)", "suggested_assignee_role": "facilities_lead"},
            {"order": 5, "title": "Communicate to staff with cadence + dedicated channel", "suggested_assignee_role": "comms_lead"},
            {"order": 6, "title": "Customer impact analysis & supply-chain checks", "suggested_assignee_role": "operations_lead"},
            {"order": 7, "title": "Financial modeling for prolonged disruption", "suggested_assignee_role": "cfo"},
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
