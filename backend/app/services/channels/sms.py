"""SMS channel adapter — simulator-mode by default."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.communication import Communication
from app.services.channels.base import DeliveryReceipt

logger = logging.getLogger(__name__)


class SmsAdapter:
    provider = "simulator:sms"
    SMS_SEGMENT_CHARS = 160

    async def send(self, comm: Communication) -> DeliveryReceipt:
        now = datetime.now(timezone.utc).isoformat()
        segments = max(1, -(-len(comm.message) // self.SMS_SEGMENT_CHARS))  # ceil division
        logger.info("sms.simulator: would send comm=%s segments=%d", comm.id, segments)
        return {
            "status": "sent",
            "provider": self.provider,
            "sent_at_iso": now,
            "details": {
                "body_chars": len(comm.message),
                "segments": segments,
                "truncation_risk": segments > 4,
            },
        }
