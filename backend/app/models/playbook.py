from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class PlaybookCategory(str, PyEnum):
    operational = "operational"
    security = "security"
    legal = "legal"
    pr = "pr"
    supply_chain = "supply_chain"
    hr = "hr"
    financial = "financial"
    other = "other"


class Playbook(Base):
    __tablename__ = "playbook"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[PlaybookCategory] = mapped_column(
        String(20), nullable=False, default=PlaybookCategory.other
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
