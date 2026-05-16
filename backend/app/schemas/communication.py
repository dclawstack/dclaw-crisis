from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CommunicationBase(BaseModel):
    crisis_id: str
    author_id: str | None = None
    message: str
    comm_type: Literal["internal_update", "stakeholder_alert", "public_statement", "exec_brief"] = "internal_update"
    channel: Literal["app", "email", "slack", "sms"] = "app"


class CommunicationCreate(CommunicationBase):
    pass


class CommunicationUpdate(BaseModel):
    message: str | None = None
    comm_type: Literal["internal_update", "stakeholder_alert", "public_statement", "exec_brief"] | None = None
    channel: Literal["app", "email", "slack", "sms"] | None = None


class CommunicationResponse(CommunicationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
