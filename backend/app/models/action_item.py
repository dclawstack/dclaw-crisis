from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.core.utils import utc_now


class ActionItemStatus(str, PyEnum):
    pending = "pending"
    in_progress = "in_progress"
    blocked = "blocked"
    completed = "completed"


class ActionItemPriority(str, PyEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ActionItem(Base):
    __tablename__ = "action_item"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    crisis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crisis.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("team_member.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ActionItemStatus] = mapped_column(
        String(20), nullable=False, default=ActionItemStatus.pending
    )
    priority: Mapped[ActionItemPriority] = mapped_column(
        String(20), nullable=False, default=ActionItemPriority.medium
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    crisis: Mapped["Crisis"] = relationship("Crisis", back_populates="action_items", lazy="selectin")
    assignee: Mapped["TeamMember | None"] = relationship(
        "TeamMember", back_populates="assigned_actions", lazy="selectin"
    )
