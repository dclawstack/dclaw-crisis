from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class MentionSentiment(str, PyEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


class MediaMention(Base):
    __tablename__ = "media_mention"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    outlet: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)

    sentiment: Mapped[MentionSentiment | None] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    key_themes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    crisis_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("crisis.id", ondelete="SET NULL"), nullable=True, index=True
    )

    mentioned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    crisis: Mapped["Crisis | None"] = relationship("Crisis", lazy="selectin", foreign_keys=[crisis_id])
