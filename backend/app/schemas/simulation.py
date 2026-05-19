from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ScenarioType = Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"]
Severity = Literal["critical", "high", "medium", "low"]
SimStatus = Literal["draft", "running", "completed", "cancelled"]


class SimulationBase(BaseModel):
    name: str
    scenario_type: ScenarioType = "operational"
    severity: Severity = "high"
    participants: list[str] = []


class SimulationCreate(SimulationBase):
    """Optional: include `auto_generate=True` to populate scenario via AI on create."""
    auto_generate: bool = True


class SimulationResponse(SimulationBase):
    id: str
    status: SimStatus
    generated_scenario: str | None
    generated_actions: list[dict[str, Any]]
    expected_outcomes: list[str]
    operator_notes: str | None
    evaluation_summary: str | None
    score: float | None
    evaluation_breakdown: list[dict[str, Any]]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RespondRequest(BaseModel):
    operator_notes: str


class EvaluateResponse(BaseModel):
    summary: str
    score: float
    breakdown: list[dict[str, Any]]
