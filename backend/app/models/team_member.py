from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.core.utils import utc_now


class TeamMember(Base):
    __tablename__ = "team_member"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    led_crises: Mapped[list["Crisis"]] = relationship("Crisis", back_populates="lead", lazy="selectin")
    assigned_actions: Mapped[list["ActionItem"]] = relationship(
        "ActionItem", back_populates="assignee", lazy="selectin"
    )
    authored_comms: Mapped[list["Communication"]] = relationship(
        "Communication", back_populates="author", lazy="selectin"
    )
