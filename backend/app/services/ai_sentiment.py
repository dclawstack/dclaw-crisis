"""AI Sentiment Analyzer for crisis communications (PRD P1.1 Phase 2).

Analyzes a draft or sent communication and predicts how the intended audience
will react. Flags content risks the operator should address before sending
(or note for future drafts).

Different from media-monitoring (P2.3) which analyzes *external* sentiment;
this looks at *our outbound* message and predicts reception.
"""
from __future__ import annotations

from app.models.communication import Communication
from app.models.crisis import Crisis
from app.services.crisis_context import render_crisis_context
from app.services.llm import complete_json

_VALID_SENTIMENT = {"positive", "neutral", "negative", "mixed"}

SYSTEM_PROMPT = (
    "You are the DClaw Crisis communications analyst. You receive a crisis "
    "communication draft (already written by humans or AI) and predict how the "
    "intended audience will receive it. Be honest — if a message reads as "
    "defensive, evasive, or risks admitting liability, flag it.\n\n"
    "Output strict JSON:\n"
    "{\n"
    '  "sentiment": "positive" | "neutral" | "negative" | "mixed",\n'
    '  "sentiment_score": float in [-1.0, 1.0]  // -1=very negative, 0=neutral, +1=very positive (predicted audience reaction),\n'
    '  "predicted_reaction": "2-3 sentences on how the audience will likely respond",\n'
    '  "risk_flags": ["short, specific concerns to address before sending", ...]  // empty list if clean\n'
    "}\n"
    "Rules:\n"
    "- Score conservatively. Even good messages rarely warrant > 0.7 during an active crisis.\n"
    "- risk_flags should be concrete and actionable (e.g. 'avoids stating a fix timeline', 'tone too defensive').\n"
    "- Empty risk_flags is fine for clean messages."
)


async def analyze_communication(comm: Communication, crisis: Crisis) -> dict:
    context = render_crisis_context(crisis, max_actions=10, max_comms=5)
    user = (
        f"COMMUNICATION TO ANALYZE\n"
        f"  type: {comm.comm_type}\n"
        f"  channel: {comm.channel}\n"
        f"  message: \"\"\"\n{comm.message}\n\"\"\"\n\n"
        f"CRISIS CONTEXT (for reference, not for analysis):\n{context}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=600)

    sentiment = str(data.get("sentiment", "neutral")).lower()
    if sentiment not in _VALID_SENTIMENT:
        sentiment = "neutral"

    try:
        score = max(-1.0, min(1.0, float(data.get("sentiment_score", 0.0))))
    except (TypeError, ValueError):
        score = 0.0

    risk_flags = data.get("risk_flags") or []
    if not isinstance(risk_flags, list):
        risk_flags = []
    risk_flags = [str(f).strip() for f in risk_flags if str(f).strip()][:10]

    return {
        "sentiment": sentiment,
        "sentiment_score": score,
        "predicted_reaction": str(data.get("predicted_reaction") or "").strip(),
        "risk_flags": risk_flags,
    }
