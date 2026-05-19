from __future__ import annotations

from typing import Protocol, TypedDict

from app.models.communication import Communication


class DeliveryReceipt(TypedDict):
    status: str  # "sent" | "failed" | "queued"
    provider: str
    sent_at_iso: str
    details: dict


class ChannelAdapter(Protocol):
    async def send(self, comm: Communication) -> DeliveryReceipt: ...
