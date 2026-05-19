"""AI Legal Hold + Evidence Tracker (PRD P2.4).

Two related AI services bundled in one module:
- `draft_hold_notice(crisis)` — generates a hold-notice text the operator can
  send (after legal review).
- `recommend_evidence(crisis)` — suggests data sources to preserve and
  custodians to notify.

Always emits a clear disclaimer: this is not a substitute for outside counsel.
"""
from __future__ import annotations

from app.models.crisis import Crisis
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete, complete_json

DISCLAIMER = (
    "[AI-GENERATED DRAFT — NOT LEGAL ADVICE. Have outside counsel review before issuing.]"
)

_NOTICE_SYSTEM = (
    "You are drafting a legal hold / litigation hold notice for an organization "
    "responding to a crisis. The notice instructs employees to preserve "
    "documents and data relevant to the matter. Output the notice body only — "
    "no preamble, no markdown, no signatures. Length 200-400 words.\n"
    "Always begin the notice with this exact line on its own:\n"
    "[AI-GENERATED DRAFT — NOT LEGAL ADVICE. Have outside counsel review before issuing.]"
)


async def draft_hold_notice(crisis: Crisis) -> str:
    context = render_crisis_context(crisis, max_actions=15, max_comms=5)
    user = (
        "Draft a legal-hold notice for the following crisis. Identify the "
        "matter, the scope of preservation, expected duration, and the consequences "
        "of non-compliance. Be conservative and procedural — do not admit fault.\n\n"
        f"{context}"
    )
    res = await complete(_NOTICE_SYSTEM, user, temperature=0.3, max_tokens=900)
    text = res.text.strip()
    if not text.startswith("[AI-GENERATED DRAFT"):
        text = f"{DISCLAIMER}\n\n{text}"
    return text


_EVIDENCE_SYSTEM = (
    "You are the DClaw Crisis evidence-preservation advisor. Given a crisis "
    "snapshot, recommend (a) data sources to preserve and (b) custodians to "
    "notify under a legal hold. Output strict JSON.\n\n"
    "Output:\n"
    "{\n"
    '  "data_sources": [\n'
    "    {\"name\": str, \"type\": \"email\" | \"chat\" | \"document_repo\" | \"database\" | \"logs\" | \"backups\" | \"other\", "
    "\"rationale\": str}, ...\n"
    "  ],\n"
    '  "custodians": [\n'
    "    {\"role\": str, \"reason\": str}, ...\n"
    "  ],\n"
    '  "preservation_duration_days_min": int  // recommended minimum hold duration\n'
    "}\n"
    "Rules:\n"
    "- Be specific. Reference systems and roles, not generic placeholders.\n"
    "- Conservative on duration — when in doubt, recommend longer."
)


async def recommend_evidence(crisis: Crisis) -> dict:
    context = render_crisis_context(crisis, max_actions=15, max_comms=5)
    user = f"Recommend evidence preservation for this crisis:\n\n{context}"
    data = await complete_json(_EVIDENCE_SYSTEM, user, temperature=0.2, max_tokens=1200)

    ds_raw = data.get("data_sources") if isinstance(data, dict) else None
    cs_raw = data.get("custodians") if isinstance(data, dict) else None

    data_sources: list[dict] = []
    if isinstance(ds_raw, list):
        allowed_types = {"email", "chat", "document_repo", "database", "logs", "backups", "other"}
        for ds in ds_raw:
            if not isinstance(ds, dict):
                continue
            t = str(ds.get("type", "other")).lower()
            if t not in allowed_types:
                t = "other"
            data_sources.append(
                {
                    "name": str(ds.get("name") or "").strip(),
                    "type": t,
                    "rationale": str(ds.get("rationale") or "").strip(),
                }
            )

    custodians: list[dict] = []
    if isinstance(cs_raw, list):
        for c in cs_raw:
            if not isinstance(c, dict):
                continue
            custodians.append(
                {
                    "role": str(c.get("role") or "").strip(),
                    "reason": str(c.get("reason") or "").strip(),
                }
            )

    try:
        min_days = max(7, int(data.get("preservation_duration_days_min", 90)))
    except (TypeError, ValueError):
        min_days = 90

    return {
        "data_sources": data_sources,
        "custodians": custodians,
        "preservation_duration_days_min": min_days,
    }
