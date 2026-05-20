import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.object_store import get_object_store
from app.core.utils import utc_now
from app.models.legal_hold import LegalHold, LegalHoldStatus
from app.schemas.legal_hold import (
    LegalHoldCreate,
    LegalHoldResponse,
    LegalHoldUpdate,
    ReleaseRequest,
)
from app.repositories.legal_hold_repo import LegalHoldRepository
from app.services.exports import render_legal_hold_notice

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[LegalHoldResponse])
async def list_holds(
    crisis_id: str | None = None,
    active_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = LegalHoldRepository(db)
    if crisis_id:
        return await repo.list_by_crisis(crisis_id, limit, offset)
    if active_only:
        return await repo.list_active(limit, offset)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("/", response_model=LegalHoldResponse, status_code=201)
async def create_hold(payload: LegalHoldCreate, db: AsyncSession = Depends(get_db)):
    hold = LegalHold(**payload.model_dump())
    return await LegalHoldRepository(db).create(hold)


@router.get("/{hold_id}", response_model=LegalHoldResponse)
async def get_hold(hold_id: str, db: AsyncSession = Depends(get_db)):
    h = await LegalHoldRepository(db).get_by_id(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    return h


@router.put("/{hold_id}", response_model=LegalHoldResponse)
async def update_hold(hold_id: str, payload: LegalHoldUpdate, db: AsyncSession = Depends(get_db)):
    repo = LegalHoldRepository(db)
    h = await repo.get_by_id(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    if h.status != LegalHoldStatus.draft.value:
        raise HTTPException(status_code=400, detail="Cannot modify a non-draft hold; release first")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    await db.commit()
    await db.refresh(h)
    return h


@router.post("/{hold_id}/issue", response_model=LegalHoldResponse)
async def issue_hold(hold_id: str, db: AsyncSession = Depends(get_db)):
    repo = LegalHoldRepository(db)
    h = await repo.get_by_id(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    if h.status != LegalHoldStatus.draft.value:
        raise HTTPException(status_code=400, detail=f"Cannot issue a hold in status {h.status}")
    if not h.hold_notice_text:
        raise HTTPException(status_code=400, detail="hold_notice_text is required before issuing")
    h.status = LegalHoldStatus.active
    h.issued_at = utc_now()
    await db.commit()
    await db.refresh(h)
    return h


@router.post("/{hold_id}/release", response_model=LegalHoldResponse)
async def release_hold(hold_id: str, payload: ReleaseRequest, db: AsyncSession = Depends(get_db)):
    repo = LegalHoldRepository(db)
    h = await repo.get_by_id(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    if h.status != LegalHoldStatus.active.value:
        raise HTTPException(status_code=400, detail=f"Cannot release a hold in status {h.status}")
    h.status = LegalHoldStatus.released
    h.released_at = utc_now()
    h.release_reason = payload.reason
    await db.commit()
    await db.refresh(h)
    return h


@router.delete("/{hold_id}", status_code=204)
async def delete_hold(hold_id: str, db: AsyncSession = Depends(get_db)):
    repo = LegalHoldRepository(db)
    h = await repo.get_by_id(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    if h.status == LegalHoldStatus.active.value:
        raise HTTPException(status_code=400, detail="Cannot delete an active hold; release it first")
    await repo.delete(h)


class HoldExportResponse(BaseModel):
    key: str
    url: str
    backend: str
    size_bytes: int


@router.post("/{hold_id}/export", response_model=HoldExportResponse)
async def export_hold(hold_id: str, db: AsyncSession = Depends(get_db)):
    """Render the hold to a plain-text document and store in the object store.

    Returns a (presigned, when MinIO is enabled) URL the operator can hand
    off to outside counsel.
    """
    h = await LegalHoldRepository(db).get_by_id(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Legal hold not found")
    text = render_legal_hold_notice(h)
    key = f"legal-holds/{h.id}/notice.txt"
    store = get_object_store()
    store.put_text(key, text, content_type="text/plain")
    url = store.presigned_get_url(key)
    return HoldExportResponse(
        key=key,
        url=url,
        backend=getattr(store, "backend", "unknown"),
        size_bytes=len(text.encode("utf-8")),
    )
