from fastapi import APIRouter
from datetime import datetime
from uuid import uuid4
from dclaw_crisis.models import CrisisPlan, CrisisCreate

router = APIRouter()

@router.post("/plans", response_model=CrisisPlan)
async def create_item(payload: CrisisCreate):
    return CrisisPlan(
        id=str(uuid4()),
        scenario=payload.scenario,
        severity_level="high",
        response_team=["CEO", "Legal", "Comms", "IT Security"],
        communication_channels=["Email", "Slack", "Status page"],
        eta_resolution_hours=48,
        created_at=datetime.utcnow(),
    )

@router.get("/plans/{plan_id}/actions")
async def get_item(plan_id: str):
    return [{"step": 1, "action": "Assess impact"}, {"step": 2, "action": "Notify stakeholders"}, {"step": 3, "action": "Activate backup systems"}, {"step": 4, "action": "Execute recovery protocol"}, {"step": 5, "action": "Post-incident review"}]
