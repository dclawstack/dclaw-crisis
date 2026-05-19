"""AI Media Sentiment Analyzer (PRD P2.3).

Analyzes an external media mention (news headline + snippet, social post,
analyst blog) and scores it. This is *external* sentiment — distinct from
P1.1 which predicts audience reaction to our *outbound* messages.
"""
from __future__ import annotations

from app.models.media_mention import MediaMention
from app.services.llm import complete_json

_VALID_SENTIMENT = {"positive", "neutral", "negative", "mixed"}

SYSTEM_PROMPT = (
    "You are the DClaw Crisis media monitoring analyst. Given an external "
    "media mention (article, social post, analyst note), score it from the "
    "perspective of the organization being mentioned. Output strict JSON.\n\n"
    "Output schema:\n"
    "{\n"
    '  "sentiment": "positive" | "neutral" | "negative" | "mixed",\n'
    '  "sentiment_score": float in [-1.0, 1.0],\n'
    '  "key_themes": ["short phrase capturing what this mention is about", ...]  // 3-6 items\n'
    "}\n"
    "Rules:\n"
    "- Score from the org's perspective — coverage that's neutral-to-positive for the org gets positive scores.\n"
    "- key_themes should be short (under 8 words each) and concrete."
)


async def analyze_mention(mention: MediaMention) -> dict:
    user = (
        f"OUTLET: {mention.outlet}\n"
        f"HEADLINE: {mention.headline or '(no headline)'}\n"
        f"AUTHOR: {mention.author or '(unknown)'}\n"
        f"URL: {mention.url or '(none)'}\n\n"
        f"SNIPPET:\n{mention.snippet[:4000]}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=500)

    sentiment = str(data.get("sentiment", "neutral")).lower()
    if sentiment not in _VALID_SENTIMENT:
        sentiment = "neutral"

    try:
        score = max(-1.0, min(1.0, float(data.get("sentiment_score", 0.0))))
    except (TypeError, ValueError):
        score = 0.0

    themes_raw = data.get("key_themes") or []
    themes = [str(t).strip() for t in themes_raw if str(t).strip()][:6] if isinstance(themes_raw, list) else []

    return {
        "sentiment": sentiment,
        "sentiment_score": score,
        "key_themes": themes,
    }
