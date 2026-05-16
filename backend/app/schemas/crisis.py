from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CrisisBase(BaseModel):
    title: str
    description: str | None = None
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    status: Literal["detected", "assessing", "responding", "contained", "resolved", "post_mortem"] = "detected"
    category: Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"] = "other"
    lead_id: str | None = None
    detected_at: datetime | None = None
    resolved_at: datetime | None = None
    estimated_impact_usd: float | None = None


class CrisisCreate(CrisisBase):
    pass


class CrisisUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: Literal["critical", "high", "medium", "low"] | None = None
    status: Literal["detected", "assessing", "responding", "contained", "resolved", "post_mortem"] | None = None
    category: Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"] | None = None
    lead_id: str | None = None
    resolved_at: datetime | None = None
    estimated_impact_usd: float | None = None


class CrisisResponse(CrisisBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrisisDetailResponse(CrisisResponse):
    pass
