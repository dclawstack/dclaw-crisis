from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.playbook import Playbook
from app.schemas.playbook import PlaybookCreate, PlaybookUpdate, PlaybookResponse
from app.repositories.playbook_repo import PlaybookRepository

router = APIRouter()


@router.get("/", response_model=list[PlaybookResponse])
async def list_playbooks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = PlaybookRepository(db)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("/", response_model=PlaybookResponse, status_code=201)
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
