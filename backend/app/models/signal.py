from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.core.utils import utc_now


class SignalStatus(str, PyEnum):
    new = "new"
    triaged = "triaged"
    promoted = "promoted"
    dismissed = "dismissed"


class Signal(Base):
    __tablename__ = "signal"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    ai_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_recommends_promotion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[SignalStatus] = mapped_column(
        String(20), nullable=False, default=SignalStatus.new, index=True
    )
    crisis_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("crisis.id", ondelete="SET NULL"), nullable=True
    )

    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    crisis: Mapped["Crisis | None"] = relationship("Crisis", lazy="selectin", foreign_keys=[crisis_id])
