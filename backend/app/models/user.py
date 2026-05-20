from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.core.utils import utc_now


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # password_hash is nullable so users provisioned via SSO (Logto, future) don't need a local password.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # auth_provider tracks which provider created the user — "local" for password, "logto" for SSO, etc.
    auth_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="local")
    # external_id is the provider's user id (e.g. Logto sub claim) — null for local users.
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
