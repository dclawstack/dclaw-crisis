from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

StakeholderType = Literal[
    "internal", "customer", "regulator", "media", "investor", "vendor", "partner", "board", "other"
]
StakeholderImportance = Literal["critical", "high", "medium", "low"]


class StakeholderBase(BaseModel):
    name: str
    type: StakeholderType = "other"
    organization: str | None = None
    importance: StakeholderImportance = "medium"
    email: str | None = None
    phone: str | None = None
    tags: list[str] = []
    notes: str | None = None
    is_active: bool = True


class StakeholderCreate(StakeholderBase):
    pass


class StakeholderUpdate(BaseModel):
    name: str | None = None
    type: StakeholderType | None = None
    organization: str | None = None
    importance: StakeholderImportance | None = None
    email: str | None = None
    phone: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    is_active: bool | None = None


class StakeholderResponse(StakeholderBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
