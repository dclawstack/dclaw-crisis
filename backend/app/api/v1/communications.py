from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.communication import Communication
from app.schemas.communication import CommunicationCreate, CommunicationUpdate, CommunicationResponse
from app.repositories.communication_repo import CommunicationRepository

router = APIRouter()


@router.get("/", response_model=list[CommunicationResponse])
async def list_communications(
    crisis_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = CommunicationRepository(db)
    if crisis_id:
        items, _ = await repo.list_by_crisis(crisis_id, limit, offset)
    else:
        items, _ = await repo.list_all(limit, offset)
    return items


@router.post("/", response_model=CommunicationResponse, status_code=201)
async def create_communication(payload: CommunicationCreate, db: AsyncSession = Depends(get_db)):
    repo = CommunicationRepository(db)
    comm = Communication(**payload.model_dump())
    return await repo.create(comm)


@router.get("/{comm_id}", response_model=CommunicationResponse)
async def get_communication(comm_id: str, db: AsyncSession = Depends(get_db)):
    repo = CommunicationRepository(db)
    comm = await repo.get_by_id(comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return comm


@router.put("/{comm_id}", response_model=CommunicationResponse)
async def update_communication(comm_id: str, payload: CommunicationUpdate, db: AsyncSession = Depends(get_db)):
    repo = CommunicationRepository(db)
    comm = await repo.get_by_id(comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(comm, key, value)
    await db.commit()
    await db.refresh(comm)
    return comm


@router.delete("/{comm_id}", status_code=204)
async def delete_communication(comm_id: str, db: AsyncSession = Depends(get_db)):
    repo = CommunicationRepository(db)
    comm = await repo.get_by_id(comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    await repo.delete(comm)
