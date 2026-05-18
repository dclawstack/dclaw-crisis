"""AI Signal Scorer — PRD P0.2 Crisis Detection.

Takes a raw signal (text from any source) and uses an LLM to:
- decide whether it represents a real crisis vs noise
- assign severity + category
- write a one-line summary
- provide a confidence score and rationale

Output is consumed by the Signal triage pipeline. No auto-promotion happens
here; severity_high/critical with high confidence merely sets
`ai_recommends_promotion=True` for the UI to flag.
"""
from __future__ import annotations

from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis signal triage analyst. You receive raw text from "
    "monitoring sources (news, social media, internal alerts, status pages, "
    "support tickets) and decide whether each item is an actual emerging crisis "
    "for the organization. You output strict JSON only.\n\n"
    "Output schema:\n"
    "{\n"
    '  "severity": "critical" | "high" | "medium" | "low",\n'
    '  "category": "operational" | "security" | "legal" | "pr" | "supply_chain" | "hr" | "financial" | "other",\n'
    '  "confidence": float 0.0-1.0 (how confident you are in this score),\n'
    '  "summary": "one-sentence factual summary, no opinions, <300 chars",\n'
    '  "rationale": "2-3 sentences on why this severity/category",\n'
    '  "is_crisis": true | false (whether this warrants response, not just noise)\n'
    "}\n\n"
    "Rules:\n"
    "- Conservative on severity. Reserve critical for life-safety, major outages affecting >50% of users, "
    "active data breaches, regulator action, or executive-level legal exposure.\n"
    "- If the signal is benign (marketing, normal status updates, low-impact noise) set is_crisis=false and severity=low.\n"
    "- Confidence below 0.5 means you are uncertain — never above 0.9 unless the signal is unambiguous."
)


async def score_signal(*, source: str, raw_text: str, source_url: str | None = None) -> dict:
    user_parts = [
        f"SOURCE: {source}",
    ]
    if source_url:
        user_parts.append(f"URL: {source_url}")
    user_parts.append("")
    user_parts.append("RAW SIGNAL:")
    user_parts.append(raw_text[:4000])  # cap input
    user = "\n".join(user_parts)

    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.1, max_tokens=400)

    # Defensive normalization in case the model strays from the schema.
    severity = str(data.get("severity", "medium")).lower()
    if severity not in {"critical", "high", "medium", "low"}:
        severity = "medium"

    category = str(data.get("category", "other")).lower()
    allowed_cats = {"operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"}
    if category not in allowed_cats:
        category = "other"

    confidence = data.get("confidence", 0.5)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5

    return {
        "severity": severity,
        "category": category,
        "confidence": confidence,
        "summary": str(data.get("summary", ""))[:500],
        "rationale": str(data.get("rationale", "")),
        "is_crisis": bool(data.get("is_crisis", False)),
    }


def recommends_promotion(severity: str, confidence: float, is_crisis: bool) -> bool:
    """Heuristic the UI uses to flag signals that look promotion-worthy.

    Conservative: only flag if AI believes it's a crisis, severity is high/critical,
    and confidence is at least 0.6.
    """
    if not is_crisis:
        return False
    if severity not in {"critical", "high"}:
        return False
    return confidence >= 0.6
