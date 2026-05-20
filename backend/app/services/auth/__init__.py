"""Pluggable auth providers (PRD §4).

LocalProvider is the default: stores password hashes in the User table,
issues JWTs we sign ourselves. LogtoProvider is a stub for when we wire up
the Logto IdP — it'll verify JWTs against Logto's JWKS instead.

Switch via the `AUTH_PROVIDER` env var (`local` | `logto`).
"""
from app.core.config import settings
from app.services.auth.base import AuthProvider, Principal
from app.services.auth.local import LocalProvider
from app.services.auth.logto import LogtoProvider


def get_provider() -> AuthProvider:
    name = (settings.auth_provider or "local").lower()
    if name == "logto":
        return LogtoProvider()
    return LocalProvider()


__all__ = ["AuthProvider", "Principal", "get_provider"]
