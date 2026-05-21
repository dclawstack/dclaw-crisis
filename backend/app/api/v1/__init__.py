from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.api.v1 import (
    auth as auth_router_module,
    crisis, team_members, action_items, communications, playbooks,
    dashboard, copilot, signals, stakeholders, resources,
    simulations, media_mentions, legal_holds, demo,
)

# Auth endpoints (signup/signin) MUST NOT require auth themselves.
v1_router = APIRouter()
v1_router.include_router(auth_router_module.router, prefix="/auth", tags=["auth"])

# Every other v1 router requires a verified user. The dependency lifts auth
# enforcement up to the router level so individual endpoints don't have to
# remember to add `Depends(require_user)`.
_auth_deps = [Depends(require_user)]

v1_router.include_router(crisis.router, prefix="/crisis", tags=["crisis"], dependencies=_auth_deps)
v1_router.include_router(team_members.router, prefix="/team-members", tags=["team-members"], dependencies=_auth_deps)
v1_router.include_router(action_items.router, prefix="/action-items", tags=["action-items"], dependencies=_auth_deps)
v1_router.include_router(communications.router, prefix="/communications", tags=["communications"], dependencies=_auth_deps)
v1_router.include_router(playbooks.router, prefix="/playbooks", tags=["playbooks"], dependencies=_auth_deps)
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=_auth_deps)
v1_router.include_router(copilot.router, prefix="/copilot", tags=["copilot"], dependencies=_auth_deps)
v1_router.include_router(signals.router, prefix="/signals", tags=["signals"], dependencies=_auth_deps)
v1_router.include_router(stakeholders.router, prefix="/stakeholders", tags=["stakeholders"], dependencies=_auth_deps)
v1_router.include_router(resources.router, prefix="/resources", tags=["resources"], dependencies=_auth_deps)
v1_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"], dependencies=_auth_deps)
v1_router.include_router(media_mentions.router, prefix="/media-mentions", tags=["media-mentions"], dependencies=_auth_deps)
v1_router.include_router(legal_holds.router, prefix="/legal-holds", tags=["legal-holds"], dependencies=_auth_deps)
# Demo router is PUBLIC — landing-page visitors hit /status before they sign
# in. /seed and /reset are gated by ENABLE_DEMO_MODE flag instead of auth.
v1_router.include_router(demo.router, prefix="/demo", tags=["demo"])
