"""Email channel adapter — simulator-mode by default.

Replace with a real SendGrid/SES/Postmark adapter by swapping the implementation
of `send` and adding provider credentials to `app/core/config.py`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.communication import Communication
from app.services.channels.base import DeliveryReceipt

logger = logging.getLogger(__name__)


class EmailAdapter:
    provider = "simulator:email"

    async def send(self, comm: Communication) -> DeliveryReceipt:
        now = datetime.now(timezone.utc).isoformat()
        logger.info("email.simulator: would send comm=%s len=%d", comm.id, len(comm.message))
        return {
            "status": "sent",
            "provider": self.provider,
            "sent_at_iso": now,
            "details": {
                "subject_hint": comm.message[:80],
                "body_chars": len(comm.message),
                "comm_type": comm.comm_type,
            },
        }
