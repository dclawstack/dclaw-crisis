"""In-app channel adapter — comm is published to the dashboard timeline.

This is a no-op delivery: the Communication row IS the in-app record.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.communication import Communication
from app.services.channels.base import DeliveryReceipt

logger = logging.getLogger(__name__)


class AppAdapter:
    provider = "in-app"

    async def send(self, comm: Communication) -> DeliveryReceipt:
        now = datetime.now(timezone.utc).isoformat()
        logger.info("app.publish: comm=%s", comm.id)
        return {
            "status": "sent",
            "provider": self.provider,
            "sent_at_iso": now,
            "details": {
                "surface": "crisis_timeline",
                "visible_in": "/crisis/" + comm.crisis_id,
            },
        }
