from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class StakeholderType(str, PyEnum):
    internal = "internal"
    customer = "customer"
    regulator = "regulator"
    media = "media"
    investor = "investor"
    vendor = "vendor"
    partner = "partner"
    board = "board"
    other = "other"


class StakeholderImportance(str, PyEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Stakeholder(Base):
    __tablename__ = "stakeholder"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[StakeholderType] = mapped_column(
        String(20), nullable=False, default=StakeholderType.other, index=True
    )
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    importance: Mapped[StakeholderImportance] = mapped_column(
        String(20), nullable=False, default=StakeholderImportance.medium, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
