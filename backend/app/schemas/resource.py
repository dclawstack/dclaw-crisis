from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ResourceType = Literal[
    "war_room", "comm_channel", "vendor_contact", "equipment", "budget_pool",
    "on_call_roster", "external_service", "other",
]
ResourceStatus = Literal["available", "reserved", "in_use", "unavailable"]


class ResourceBase(BaseModel):
    name: str
    resource_type: ResourceType = "other"
    status: ResourceStatus = "available"
    capacity: str | None = None
    location: str | None = None
    attributes: dict[str, Any] = {}
    notes: str | None = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: str | None = None
    resource_type: ResourceType | None = None
    status: ResourceStatus | None = None
    capacity: str | None = None
    location: str | None = None
    attributes: dict[str, Any] | None = None
    notes: str | None = None


class ResourceResponse(ResourceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
