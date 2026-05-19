from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class ResourceType(str, PyEnum):
    war_room = "war_room"
    comm_channel = "comm_channel"
    vendor_contact = "vendor_contact"
    equipment = "equipment"
    budget_pool = "budget_pool"
    on_call_roster = "on_call_roster"
    external_service = "external_service"
    other = "other"


class ResourceStatus(str, PyEnum):
    available = "available"
    reserved = "reserved"
    in_use = "in_use"
    unavailable = "unavailable"


class Resource(Base):
    __tablename__ = "resource"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(
        String(30), nullable=False, default=ResourceType.other, index=True
    )
    status: Mapped[ResourceStatus] = mapped_column(
        String(20), nullable=False, default=ResourceStatus.available, index=True
    )
    capacity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
