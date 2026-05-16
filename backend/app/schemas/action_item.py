from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ActionItemBase(BaseModel):
    crisis_id: str
    title: str
    description: str | None = None
    assignee_id: str | None = None
    status: Literal["pending", "in_progress", "blocked", "completed"] = "pending"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    due_at: datetime | None = None


class ActionItemCreate(ActionItemBase):
    pass


class ActionItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: str | None = None
    status: Literal["pending", "in_progress", "blocked", "completed"] | None = None
    priority: Literal["critical", "high", "medium", "low"] | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None


class ActionItemResponse(ActionItemBase):
    id: str
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
