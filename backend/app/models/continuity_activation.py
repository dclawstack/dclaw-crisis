from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class ActivationStatus(str, PyEnum):
    pending = "pending"
    activated = "activated"
    failed = "failed"
    cancelled = "cancelled"


class ContinuityActivation(Base):
    __tablename__ = "continuity_activation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    crisis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crisis.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bcp_plan_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bcp_plan_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ActivationStatus] = mapped_column(
        String(20), nullable=False, default=ActivationStatus.pending, index=True
    )
    provider: Mapped[str] = mapped_column(String(60), nullable=False, default="simulator")
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    crisis: Mapped["Crisis"] = relationship("Crisis", lazy="selectin", foreign_keys=[crisis_id])
