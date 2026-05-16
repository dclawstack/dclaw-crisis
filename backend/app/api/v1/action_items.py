from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.models.action_item import ActionItem
from app.schemas.action_item import ActionItemCreate, ActionItemUpdate, ActionItemResponse
from app.repositories.action_item_repo import ActionItemRepository

router = APIRouter()


@router.get("/", response_model=list[ActionItemResponse])
async def list_action_items(
    crisis_id: str | None = None,
    assignee_id: str | None = None,
    status: Literal["pending", "in_progress", "blocked", "completed"] | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = ActionItemRepository(db)
    if crisis_id:
        items, _ = await repo.list_by_crisis(crisis_id, limit, offset)
    elif assignee_id:
        items, _ = await repo.list_by_assignee(assignee_id, limit, offset)
    else:
        items, _ = await repo.list_all(limit, offset)
    if status:
        items = [i for i in items if i.status == status]
    return items


@router.post("/", response_model=ActionItemResponse, status_code=201)
async def create_action_item(payload: ActionItemCreate, db: AsyncSession = Depends(get_db)):
    repo = ActionItemRepository(db)
    item = ActionItem(**payload.model_dump())
    return await repo.create(item)


@router.get("/{item_id}", response_model=ActionItemResponse)
async def get_action_item(item_id: str, db: AsyncSession = Depends(get_db)):
    repo = ActionItemRepository(db)
    item = await repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.put("/{item_id}", response_model=ActionItemResponse)
async def update_action_item(item_id: str, payload: ActionItemUpdate, db: AsyncSession = Depends(get_db)):
    repo = ActionItemRepository(db)
    item = await repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_action_item(item_id: str, db: AsyncSession = Depends(get_db)):
    repo = ActionItemRepository(db)
    item = await repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    await repo.delete(item)
