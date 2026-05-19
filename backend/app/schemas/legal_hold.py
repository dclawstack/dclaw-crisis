from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

HoldStatus = Literal["draft", "active", "released"]


class LegalHoldBase(BaseModel):
    crisis_id: str | None = None
    title: str
    scope_description: str | None = None
    custodians: list[dict[str, Any]] = []
    data_sources: list[str] = []
    hold_notice_text: str | None = None
    issued_by: str | None = None


class LegalHoldCreate(LegalHoldBase):
    pass


class LegalHoldUpdate(BaseModel):
    title: str | None = None
    scope_description: str | None = None
    custodians: list[dict[str, Any]] | None = None
    data_sources: list[str] | None = None
    hold_notice_text: str | None = None
    issued_by: str | None = None


class LegalHoldResponse(LegalHoldBase):
    id: str
    status: HoldStatus
    issued_at: datetime | None
    released_at: datetime | None
    release_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReleaseRequest(BaseModel):
    reason: str | None = None
