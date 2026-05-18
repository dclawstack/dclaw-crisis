from fastapi import APIRouter

from app.api.v1 import crisis, team_members, action_items, communications, playbooks, dashboard, copilot, signals

v1_router = APIRouter()
v1_router.include_router(crisis.router, prefix="/crisis", tags=["crisis"])
v1_router.include_router(team_members.router, prefix="/team-members", tags=["team-members"])
v1_router.include_router(action_items.router, prefix="/action-items", tags=["action-items"])
v1_router.include_router(communications.router, prefix="/communications", tags=["communications"])
v1_router.include_router(playbooks.router, prefix="/playbooks", tags=["playbooks"])
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
v1_router.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
v1_router.include_router(signals.router, prefix="/signals", tags=["signals"])
