from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base
from app.core.utils import utc_now


class SimulationStatus(str, PyEnum):
    draft = "draft"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"


class Simulation(Base):
    __tablename__ = "simulation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(40), nullable=False, default="operational", index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="high")
    generated_scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_actions: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    expected_outcomes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[SimulationStatus] = mapped_column(
        String(20), nullable=False, default=SimulationStatus.draft, index=True
    )
    participants: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    operator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation_breakdown: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
