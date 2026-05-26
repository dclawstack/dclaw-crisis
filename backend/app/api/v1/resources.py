from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.models.resource import Resource, ResourceStatus, ResourceType
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from app.repositories.resource_repo import ResourceRepository

router = APIRouter()


@router.get("", response_model=list[ResourceResponse])
async def list_resources(
    status: Literal["available", "reserved", "in_use", "unavailable"] | None = None,
    resource_type: Literal[
        "war_room", "comm_channel", "vendor_contact", "equipment", "budget_pool",
        "on_call_roster", "external_service", "other",
    ] | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceRepository(db)
    if status:
        return await repo.list_by_status(ResourceStatus(status), limit, offset)
    if resource_type:
        return await repo.list_by_type(ResourceType(resource_type), limit, offset)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("", response_model=ResourceResponse, status_code=201)
async def create_resource(payload: ResourceCreate, db: AsyncSession = Depends(get_db)):
    repo = ResourceRepository(db)
    r = Resource(**payload.model_dump())
    return await repo.create(r)


@router.get("/{r_id}", response_model=ResourceResponse)
async def get_resource(r_id: str, db: AsyncSession = Depends(get_db)):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(r_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    return r


@router.put("/{r_id}", response_model=ResourceResponse)
async def update_resource(r_id: str, payload: ResourceUpdate, db: AsyncSession = Depends(get_db)):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(r_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    await db.commit()
    await db.refresh(r)
    return r


@router.delete("/{r_id}", status_code=204)
async def delete_resource(r_id: str, db: AsyncSession = Depends(get_db)):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(r_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    await repo.delete(r)
