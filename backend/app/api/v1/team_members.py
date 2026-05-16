from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.team_member import TeamMember
from app.schemas.team_member import TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
from app.repositories.team_member_repo import TeamMemberRepository

router = APIRouter()


@router.get("/", response_model=list[TeamMemberResponse])
async def list_team_members(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = TeamMemberRepository(db)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("/", response_model=TeamMemberResponse, status_code=201)
async def create_team_member(payload: TeamMemberCreate, db: AsyncSession = Depends(get_db)):
    repo = TeamMemberRepository(db)
    member = TeamMember(**payload.model_dump())
    return await repo.create(member)


@router.get("/{member_id}", response_model=TeamMemberResponse)
async def get_team_member(member_id: str, db: AsyncSession = Depends(get_db)):
    repo = TeamMemberRepository(db)
    member = await repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@router.put("/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(member_id: str, payload: TeamMemberUpdate, db: AsyncSession = Depends(get_db)):
    repo = TeamMemberRepository(db)
    member = await repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
async def delete_team_member(member_id: str, db: AsyncSession = Depends(get_db)):
    repo = TeamMemberRepository(db)
    member = await repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    await repo.delete(member)
