from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.models.stakeholder import Stakeholder, StakeholderType
from app.schemas.stakeholder import StakeholderCreate, StakeholderUpdate, StakeholderResponse
from app.repositories.stakeholder_repo import StakeholderRepository

router = APIRouter()


@router.get("", response_model=list[StakeholderResponse])
async def list_stakeholders(
    type: Literal["internal", "customer", "regulator", "media", "investor", "vendor", "partner", "board", "other"] | None = None,
    active_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = StakeholderRepository(db)
    if type:
        return await repo.list_by_type(StakeholderType(type), limit, offset)
    if active_only:
        return await repo.list_active(limit, offset)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("", response_model=StakeholderResponse, status_code=201)
async def create_stakeholder(payload: StakeholderCreate, db: AsyncSession = Depends(get_db)):
    repo = StakeholderRepository(db)
    s = Stakeholder(**payload.model_dump())
    return await repo.create(s)


@router.get("/{sh_id}", response_model=StakeholderResponse)
async def get_stakeholder(sh_id: str, db: AsyncSession = Depends(get_db)):
    repo = StakeholderRepository(db)
    s = await repo.get_by_id(sh_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    return s


@router.put("/{sh_id}", response_model=StakeholderResponse)
async def update_stakeholder(sh_id: str, payload: StakeholderUpdate, db: AsyncSession = Depends(get_db)):
    repo = StakeholderRepository(db)
    s = await repo.get_by_id(sh_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/{sh_id}", status_code=204)
async def delete_stakeholder(sh_id: str, db: AsyncSession = Depends(get_db)):
    repo = StakeholderRepository(db)
    s = await repo.get_by_id(sh_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    await repo.delete(s)
