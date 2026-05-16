from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.models.crisis import Crisis
from app.schemas.crisis import CrisisCreate, CrisisUpdate, CrisisResponse
from app.repositories.crisis_repo import CrisisRepository

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
