from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.utils import utc_now
from app.models.communication import Communication, DeliveryStatus
from app.schemas.communication import CommunicationCreate, CommunicationUpdate, CommunicationResponse
from app.repositories.communication_repo import CommunicationRepository
from app.repositories.crisis_repo import CrisisRepository
from app.services.ai_comm_draft import draft_communication
from app.services.ai_sentiment import analyze_communication
from app.services.channels import dispatch
from app.services.channels.dispatcher import UnknownChannelError
from app.services.llm import LLMUnavailableError

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


class DraftRequest(BaseModel):
    crisis_id: str
    comm_type: str = "internal_update"
    channel: str = "app"
    audience: str | None = None
    extra_context: str | None = None


class DraftResponse(BaseModel):
    draft: str
    comm_type: str
    channel: str


@router.post("/draft", response_model=DraftResponse)
async def draft_endpoint(payload: DraftRequest, db: AsyncSession = Depends(get_db)):
    crisis = await CrisisRepository(db).get_by_id(payload.crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        text = await draft_communication(
            crisis,
            comm_type=payload.comm_type,
            channel=payload.channel,
            audience=payload.audience,
            extra_context=payload.extra_context,
        )
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return DraftResponse(draft=text, comm_type=payload.comm_type, channel=payload.channel)


@router.post("/{comm_id}/send", response_model=CommunicationResponse)
async def send_communication(comm_id: str, db: AsyncSession = Depends(get_db)):
    """Dispatch the communication via its channel adapter. Records delivery_log + sent_at."""
    repo = CommunicationRepository(db)
    comm = await repo.get_by_id(comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    if comm.delivery_status == DeliveryStatus.sent.value:
        raise HTTPException(status_code=400, detail="Communication has already been sent")

    try:
        receipt = await dispatch(comm)
    except UnknownChannelError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        comm.delivery_status = DeliveryStatus.failed
        comm.delivery_log = {"error": str(exc), "error_type": type(exc).__name__}
        await db.commit()
        await db.refresh(comm)
        raise HTTPException(status_code=502, detail=f"Channel dispatch failed: {exc}")

    comm.delivery_status = DeliveryStatus.sent
    comm.sent_at = utc_now()
    comm.delivery_log = dict(receipt)
    await db.commit()
    await db.refresh(comm)
    return comm


class SentimentResponse(BaseModel):
    sentiment: str
    sentiment_score: float
    predicted_reaction: str
    risk_flags: list[str]
    analyzed_at: datetime


@router.post("/{comm_id}/analyze-sentiment", response_model=SentimentResponse)
async def analyze_sentiment_endpoint(comm_id: str, db: AsyncSession = Depends(get_db)):
    """Run AI sentiment analysis on the communication and persist results."""
    repo = CommunicationRepository(db)
    comm = await repo.get_by_id(comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    crisis = await CrisisRepository(db).get_by_id(comm.crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")

    try:
        result = await analyze_communication(comm, crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")

    comm.sentiment = result["sentiment"]
    comm.sentiment_score = result["sentiment_score"]
    comm.predicted_reaction = result["predicted_reaction"]
    comm.risk_flags = result["risk_flags"]
    comm.sentiment_analyzed_at = utc_now()
    await db.commit()
    await db.refresh(comm)
    return SentimentResponse(
        sentiment=comm.sentiment,
        sentiment_score=comm.sentiment_score,
        predicted_reaction=comm.predicted_reaction or "",
        risk_flags=comm.risk_flags,
        analyzed_at=comm.sentiment_analyzed_at,
    )
