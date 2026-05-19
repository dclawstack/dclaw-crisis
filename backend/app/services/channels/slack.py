"""Slack channel adapter — simulator-mode by default."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.communication import Communication
from app.services.channels.base import DeliveryReceipt

logger = logging.getLogger(__name__)


class SlackAdapter:
    provider = "simulator:slack"

    async def send(self, comm: Communication) -> DeliveryReceipt:
        now = datetime.now(timezone.utc).isoformat()
        logger.info("slack.simulator: would post comm=%s", comm.id)
        return {
            "status": "sent",
            "provider": self.provider,
            "sent_at_iso": now,
            "details": {
                "channel_hint": f"#crisis-{comm.crisis_id[:8]}",
                "body_chars": len(comm.message),
                "blocks": 1,
            },
        }
