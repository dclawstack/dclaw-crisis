from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.core.utils import utc_now


class Severity(str, PyEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class CrisisStatus(str, PyEnum):
    detected = "detected"
    assessing = "assessing"
    responding = "responding"
    contained = "contained"
    resolved = "resolved"
    post_mortem = "post_mortem"


class CrisisCategory(str, PyEnum):
    operational = "operational"
    security = "security"
    legal = "legal"
    pr = "pr"
    supply_chain = "supply_chain"
    hr = "hr"
    financial = "financial"
    other = "other"


class Crisis(Base):
    __tablename__ = "crisis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[Severity] = mapped_column(String(20), nullable=False, default=Severity.medium)
    status: Mapped[CrisisStatus] = mapped_column(String(20), nullable=False, default=CrisisStatus.detected)
    category: Mapped[CrisisCategory] = mapped_column(String(20), nullable=False, default=CrisisCategory.other)
    lead_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("team_member.id", ondelete="SET NULL"), nullable=True
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimated_impact_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    lead: Mapped["TeamMember | None"] = relationship("TeamMember", back_populates="led_crises", lazy="selectin")
    action_items: Mapped[list["ActionItem"]] = relationship(
        "ActionItem", back_populates="crisis", lazy="selectin", cascade="all, delete-orphan"
    )
    communications: Mapped[list["Communication"]] = relationship(
        "Communication", back_populates="crisis", lazy="selectin", cascade="all, delete-orphan"
    )
