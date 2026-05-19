"""Pick the right adapter for a Communication and dispatch it."""
from __future__ import annotations

from app.models.communication import Communication
from app.services.channels.app import AppAdapter
from app.services.channels.base import DeliveryReceipt
from app.services.channels.email import EmailAdapter
from app.services.channels.slack import SlackAdapter
from app.services.channels.sms import SmsAdapter

_ADAPTERS = {
    "email": EmailAdapter(),
    "slack": SlackAdapter(),
    "sms": SmsAdapter(),
    "app": AppAdapter(),
}


class UnknownChannelError(RuntimeError):
    pass


async def dispatch(comm: Communication) -> DeliveryReceipt:
    adapter = _ADAPTERS.get(comm.channel)
    if adapter is None:
        raise UnknownChannelError(f"No adapter registered for channel '{comm.channel}'")
    return await adapter.send(comm)
