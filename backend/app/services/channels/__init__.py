"""Channel adapters for PRD P1.1 — distribute crisis communications.

Simulator-pattern: each adapter logs the payload and returns a delivery receipt
with timestamp and channel-specific metadata. Real provider integrations
(SendGrid, Slack webhook, Twilio) can be added by replacing individual adapters
without changing the dispatcher contract.
"""
from app.services.channels.dispatcher import dispatch

__all__ = ["dispatch"]
