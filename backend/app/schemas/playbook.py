from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlaybookStep(BaseModel):
    order: int
    title: str
    description: str | None = None
    suggested_assignee_role: str | None = None


class PlaybookBase(BaseModel):
    name: str
    category: Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"] = "other"
    description: str | None = None
    steps: list[PlaybookStep] = []


class PlaybookCreate(PlaybookBase):
    pass


class PlaybookUpdate(BaseModel):
    name: str | None = None
    category: Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"] | None = None
    description: str | None = None
    steps: list[PlaybookStep] | None = None


class PlaybookResponse(PlaybookBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
