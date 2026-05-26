import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.action_item import ActionItem
from app.models.crisis import Crisis
from app.models.playbook import Playbook
from app.schemas.playbook import PlaybookCreate, PlaybookUpdate, PlaybookResponse
from app.schemas.crisis import CrisisResponse
from app.repositories.playbook_repo import PlaybookRepository
from app.repositories.crisis_repo import CrisisRepository
from app.services.playbook_seed import seed_playbooks
from app.services.ai_playbook_customizer import customize_steps
from app.services.llm import LLMUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[PlaybookResponse])
async def list_playbooks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = PlaybookRepository(db)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("", response_model=PlaybookResponse, status_code=201)
async def create_playbook(payload: PlaybookCreate, db: AsyncSession = Depends(get_db)):
    repo = PlaybookRepository(db)
    pb = Playbook(**payload.model_dump())
    return await repo.create(pb)


@router.get("/{pb_id}", response_model=PlaybookResponse)
async def get_playbook(pb_id: str, db: AsyncSession = Depends(get_db)):
    repo = PlaybookRepository(db)
    pb = await repo.get_by_id(pb_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return pb


@router.put("/{pb_id}", response_model=PlaybookResponse)
async def update_playbook(pb_id: str, payload: PlaybookUpdate, db: AsyncSession = Depends(get_db)):
    repo = PlaybookRepository(db)
    pb = await repo.get_by_id(pb_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(pb, key, value)
    await db.commit()
    await db.refresh(pb)
    return pb


@router.delete("/{pb_id}", status_code=204)
async def delete_playbook(pb_id: str, db: AsyncSession = Depends(get_db)):
    repo = PlaybookRepository(db)
    pb = await repo.get_by_id(pb_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    await repo.delete(pb)


class SeedResponse(BaseModel):
    created: int
    skipped: int


@router.post("/seed", response_model=SeedResponse)
async def seed_endpoint(db: AsyncSession = Depends(get_db)):
    """Seed the standard response-plan templates (idempotent)."""
    counts = await seed_playbooks(db)
    return SeedResponse(**counts)


class InstantiateRequest(BaseModel):
    title: str
    description: str | None = None
    severity: str = "medium"
    incident_context: str | None = None
    ai_customize: bool = False


class InstantiateResponse(BaseModel):
    crisis: CrisisResponse
    ai_customized: bool


@router.post("/{pb_id}/instantiate", response_model=InstantiateResponse, status_code=201)
async def instantiate_playbook(
    pb_id: str, payload: InstantiateRequest, db: AsyncSession = Depends(get_db)
):
    """Create a Crisis from a Playbook template, populating action items from steps.

    If `ai_customize=true` and `incident_context` is provided, an AI pass rewrites
    each step's title/description to be specific to the incident.
    """
    pb_repo = PlaybookRepository(db)
    pb = await pb_repo.get_by_id(pb_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")

    customized_steps: list[dict] | None = None
    ai_customized = False
    if payload.ai_customize and payload.incident_context and payload.incident_context.strip():
        try:
            customized_steps = await customize_steps(pb, payload.incident_context)
            ai_customized = True
        except LLMUnavailableError as exc:
            logger.warning("AI customization unavailable, falling back to generic steps: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI customization failed (%s): %s", type(exc).__name__, exc)

    crisis_repo = CrisisRepository(db)
    crisis = Crisis(
        title=payload.title,
        description=payload.description or pb.description,
        severity=payload.severity,
        status="responding",
        category=pb.category,
    )
    crisis = await crisis_repo.create(crisis)

    source_steps = customized_steps if customized_steps else (pb.steps or [])
    for step in sorted(source_steps, key=lambda s: s.get("order", 0)):
        action = ActionItem(
            crisis_id=crisis.id,
            title=step.get("title", "Untitled step"),
            description=step.get("description"),
            status="pending",
            priority="medium",
        )
        db.add(action)
    await db.commit()
    await db.refresh(crisis)
    return InstantiateResponse(crisis=crisis, ai_customized=ai_customized)
