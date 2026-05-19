from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ActivationStatusLit = Literal["pending", "activated", "failed", "cancelled"]


class ContinuityActivationResponse(BaseModel):
    id: str
    crisis_id: str
    bcp_plan_id: str | None
    bcp_plan_name: str | None
    status: ActivationStatusLit
    provider: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    error_message: str | None
    activated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivateBCPRequest(BaseModel):
    bcp_plan_id: str | None = None
    bcp_plan_name: str | None = None
    notes: str | None = None
