from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class LegalHoldStatus(str, PyEnum):
    draft = "draft"
    active = "active"
    released = "released"


class LegalHold(Base):
    __tablename__ = "legal_hold"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    crisis_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("crisis.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    custodians: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    data_sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    hold_notice_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LegalHoldStatus] = mapped_column(
        String(20), nullable=False, default=LegalHoldStatus.draft, index=True
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    issued_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    crisis: Mapped["Crisis | None"] = relationship("Crisis", lazy="selectin", foreign_keys=[crisis_id])
