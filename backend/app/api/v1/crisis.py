from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.models.crisis import Crisis
from app.schemas.crisis import CrisisCreate, CrisisUpdate, CrisisResponse
from app.repositories.crisis_repo import CrisisRepository
from app.services.ai_summarizer import summarize_crisis
from app.services.ai_recommender import recommend_next_action
from app.services.llm import LLMUnavailableError

router = APIRouter()


@router.get("/", response_model=list[CrisisResponse])
async def list_crises(
    status: Literal["detected", "assessing", "responding", "contained", "resolved", "post_mortem"] | None = None,
    severity: Literal["critical", "high", "medium", "low"] | None = None,
    category: Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = CrisisRepository(db)
    if status:
        from app.models.crisis import CrisisStatus
        items, _ = await repo.list_by_status(CrisisStatus(status), limit, offset)
    elif severity:
        from app.models.crisis import Severity
        items, _ = await repo.list_by_severity(Severity(severity), limit, offset)
    elif category:
        from app.models.crisis import CrisisCategory
        items, _ = await repo.list_by_category(CrisisCategory(category), limit, offset)
    else:
        items, _ = await repo.list_all(limit, offset)
    return items


@router.post("/", response_model=CrisisResponse, status_code=201)
async def create_crisis(payload: CrisisCreate, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    data = payload.model_dump()
    if data.get("detected_at") is None:
        from app.core.utils import utc_now
        data["detected_at"] = utc_now()
    crisis = Crisis(**data)
    return await repo.create(crisis)


@router.get("/{crisis_id}", response_model=CrisisResponse)
async def get_crisis(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_with_actions(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    return crisis


@router.put("/{crisis_id}", response_model=CrisisResponse)
async def update_crisis(crisis_id: str, payload: CrisisUpdate, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(crisis, key, value)
    await db.commit()
    await db.refresh(crisis)
    return crisis


@router.delete("/{crisis_id}", status_code=204)
async def delete_crisis(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    await repo.delete(crisis)


class SummaryResponse(BaseModel):
    summary: str


class NextActionResponse(BaseModel):
    title: str
    description: str
    priority: str
    rationale: str
    suggested_assignee_role: str


@router.post("/{crisis_id}/summarize", response_model=SummaryResponse)
async def summarize(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        text = await summarize_crisis(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return SummaryResponse(summary=text)


@router.get("/{crisis_id}/next-action", response_model=NextActionResponse)
async def next_action(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await recommend_next_action(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return NextActionResponse(**data)
