"""AI Simulation Evaluator (PRD P2.1) — scores operator response against expected outcomes."""
from __future__ import annotations

from app.models.simulation import Simulation
from app.services.llm import complete_json

SYSTEM_PROMPT = (
    "You are the DClaw Crisis simulation facilitator. You receive: the original "
    "scenario, the expected actions, the expected outcomes, and the operator's "
    "written response describing what they did. Evaluate honestly — note what "
    "they did well, what they missed, and produce a score from 0.0 to 1.0.\n\n"
    "Output strict JSON:\n"
    "{\n"
    '  "summary": "2-3 sentence overall assessment",\n'
    '  "score": float 0.0-1.0,\n'
    '  "breakdown": [\n'
    "    {\n"
    '      "expected_outcome": str,\n'
    '      "achieved": "yes" | "partial" | "no",\n'
    '      "comment": "specific note tied to the operator response"\n'
    "    }, ...\n"
    "  ]\n"
    "}\n"
    "Rules:\n"
    "- Be specific. Reference the operator's text.\n"
    "- Reserve scores > 0.85 for unambiguous success across all outcomes.\n"
    "- Reserve scores < 0.3 for serious gaps (skipped containment, missed legal notification, etc.)."
)


async def evaluate_simulation(sim: Simulation) -> dict:
    user = (
        f"SCENARIO:\n{sim.generated_scenario or '(no scenario captured)'}\n\n"
        f"EXPECTED ACTIONS:\n{sim.generated_actions}\n\n"
        f"EXPECTED OUTCOMES:\n{sim.expected_outcomes}\n\n"
        f"OPERATOR RESPONSE NOTES:\n{sim.operator_notes or '(none provided)'}"
    )
    data = await complete_json(SYSTEM_PROMPT, user, temperature=0.2, max_tokens=1500)

    try:
        score = max(0.0, min(1.0, float(data.get("score", 0.0))))
    except (TypeError, ValueError):
        score = 0.0

    breakdown_raw = data.get("breakdown") if isinstance(data, dict) else None
    breakdown: list[dict] = []
    if isinstance(breakdown_raw, list):
        for b in breakdown_raw:
            if not isinstance(b, dict):
                continue
            breakdown.append(
                {
                    "expected_outcome": str(b.get("expected_outcome") or "").strip(),
                    "achieved": str(b.get("achieved", "no")).lower() if str(b.get("achieved", "")).lower() in {"yes", "partial", "no"} else "no",
                    "comment": str(b.get("comment") or "").strip(),
                }
            )

    return {
        "summary": str(data.get("summary") or "").strip(),
        "score": score,
        "breakdown": breakdown,
    }
