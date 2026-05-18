from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["critical", "high", "medium", "low"]
Category = Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"]
Status = Literal["new", "triaged", "promoted", "dismissed"]


class SignalIngest(BaseModel):
    """Payload any integration (webhook, manual entry, internal monitor) sends."""

    source: str = Field(..., max_length=120, description='Free-text identifier of the source e.g. "rss:hackernews", "webhook:datadog", "manual"')
    source_url: str | None = None
    raw_text: str
    detected_at: datetime | None = None
    auto_score: bool = True


class SignalScoreResult(BaseModel):
    severity: Severity
    category: Category
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str = Field(..., max_length=500)
    rationale: str
    is_crisis: bool


class SignalResponse(BaseModel):
    id: str
    source: str
    source_url: str | None
    raw_text: str
    ai_summary: str | None
    ai_severity: Severity | None
    ai_category: Category | None
    ai_confidence: float | None
    ai_rationale: str | None
    ai_recommends_promotion: bool
    status: Status
    crisis_id: str | None
    detected_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignalPromoteRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    severity_override: Severity | None = None
