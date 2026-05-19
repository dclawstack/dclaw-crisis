from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class CommType(str, PyEnum):
    internal_update = "internal_update"
    stakeholder_alert = "stakeholder_alert"
    public_statement = "public_statement"
    exec_brief = "exec_brief"


class CommChannel(str, PyEnum):
    app = "app"
    email = "email"
    slack = "slack"
    sms = "sms"


class DeliveryStatus(str, PyEnum):
    pending = "pending"
    queued = "queued"
    sent = "sent"
    failed = "failed"


class Sentiment(str, PyEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


class Communication(Base):
    __tablename__ = "communication"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    crisis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crisis.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("team_member.id", ondelete="SET NULL"), nullable=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    comm_type: Mapped[CommType] = mapped_column(
        String(30), nullable=False, default=CommType.internal_update
    )
    channel: Mapped[CommChannel] = mapped_column(
        String(20), nullable=False, default=CommChannel.app
    )

    # Delivery tracking (PRD P1.1 Phase 2)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        String(20), nullable=False, default=DeliveryStatus.pending, index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivery_log: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Sentiment analysis (PRD P1.1 Phase 2)
    sentiment: Mapped[Sentiment | None] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    predicted_reaction: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    crisis: Mapped["Crisis"] = relationship("Crisis", back_populates="communications", lazy="selectin")
    author: Mapped["TeamMember | None"] = relationship(
        "TeamMember", back_populates="authored_comms", lazy="selectin"
    )
