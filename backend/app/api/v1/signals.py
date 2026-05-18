import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.core.utils import utc_now
from app.models.crisis import Crisis
from app.models.signal import Signal, SignalStatus
from app.schemas.signal import (
    SignalIngest,
    SignalResponse,
    SignalPromoteRequest,
)
from app.repositories.signal_repo import SignalRepository
from app.services.ai_signal_scorer import recommends_promotion, score_signal
from app.services.llm import LLMUnavailableError

logger = logging.getLogger(__name__)
router = APIRouter()


async def _apply_score(signal: Signal, db: AsyncSession) -> None:
    """Score a signal in-place and commit. Swallows LLM errors so ingestion never fails."""
    try:
        result = await score_signal(
            source=signal.source,
            raw_text=signal.raw_text,
            source_url=signal.source_url,
        )
    except LLMUnavailableError as exc:
        logger.warning("signal %s: LLM unavailable, leaving unscored: %s", signal.id, exc)
        return
    except Exception as exc:  # noqa: BLE001
        logger.warning("signal %s: scoring failed (%s): %s", signal.id, type(exc).__name__, exc)
        return
    signal.ai_severity = result["severity"]
    signal.ai_category = result["category"]
    signal.ai_confidence = result["confidence"]
    signal.ai_summary = result["summary"]
    signal.ai_rationale = result["rationale"]
    signal.ai_recommends_promotion = recommends_promotion(
        result["severity"], result["confidence"], result["is_crisis"]
    )
    await db.commit()
    await db.refresh(signal)


@router.post("/", response_model=SignalResponse, status_code=201)
async def ingest_signal(payload: SignalIngest, db: AsyncSession = Depends(get_db)):
    """Ingest a raw signal from any source (webhook, manual entry, internal monitor)."""
    signal = Signal(
        source=payload.source,
        source_url=payload.source_url,
        raw_text=payload.raw_text,
        detected_at=payload.detected_at or utc_now(),
        status=SignalStatus.new,
    )
    repo = SignalRepository(db)
    signal = await repo.create(signal)
    if payload.auto_score:
        await _apply_score(signal, db)
    return signal


@router.get("/", response_model=list[SignalResponse])
async def list_signals(
    status: Literal["new", "triaged", "promoted", "dismissed"] | None = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = SignalRepository(db)
    if status:
        items, _ = await repo.list_by_status(SignalStatus(status), limit, offset)
    else:
        items, _ = await repo.list_all(limit, offset)
    return items


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str, db: AsyncSession = Depends(get_db)):
    repo = SignalRepository(db)
    signal = await repo.get_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.post("/{signal_id}/rescore", response_model=SignalResponse)
async def rescore_signal(signal_id: str, db: AsyncSession = Depends(get_db)):
    repo = SignalRepository(db)
    signal = await repo.get_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    try:
        result = await score_signal(
            source=signal.source, raw_text=signal.raw_text, source_url=signal.source_url
        )
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    signal.ai_severity = result["severity"]
    signal.ai_category = result["category"]
    signal.ai_confidence = result["confidence"]
    signal.ai_summary = result["summary"]
    signal.ai_rationale = result["rationale"]
    signal.ai_recommends_promotion = recommends_promotion(
        result["severity"], result["confidence"], result["is_crisis"]
    )
    await db.commit()
    await db.refresh(signal)
    return signal


@router.post("/{signal_id}/triage", response_model=SignalResponse)
async def triage_signal(signal_id: str, db: AsyncSession = Depends(get_db)):
    """Mark a signal as acknowledged but not yet acted on."""
    repo = SignalRepository(db)
    signal = await repo.get_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    if signal.status not in (SignalStatus.new, SignalStatus.triaged):
        raise HTTPException(status_code=400, detail=f"Cannot triage a signal in status {signal.status}")
    signal.status = SignalStatus.triaged
    await db.commit()
    await db.refresh(signal)
    return signal


@router.post("/{signal_id}/dismiss", response_model=SignalResponse)
async def dismiss_signal(signal_id: str, db: AsyncSession = Depends(get_db)):
    repo = SignalRepository(db)
    signal = await repo.get_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    if signal.status == SignalStatus.promoted:
        raise HTTPException(status_code=400, detail="Cannot dismiss a signal already promoted to a crisis")
    signal.status = SignalStatus.dismissed
    await db.commit()
    await db.refresh(signal)
    return signal


@router.post("/{signal_id}/promote", response_model=SignalResponse, status_code=201)
async def promote_signal(
    signal_id: str, payload: SignalPromoteRequest, db: AsyncSession = Depends(get_db)
):
    """Promote a signal to a Crisis. Always requires human approval (no auto-promotion)."""
    repo = SignalRepository(db)
    signal = await repo.get_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    if signal.status == SignalStatus.promoted:
        raise HTTPException(status_code=400, detail="Signal already promoted")

    title = payload.title or signal.ai_summary or signal.raw_text[:120]
    description_parts = [payload.description] if payload.description else []
    description_parts.append(f"Source: {signal.source}")
    if signal.source_url:
        description_parts.append(f"URL: {signal.source_url}")
    description_parts.append("")
    description_parts.append("Original signal:")
    description_parts.append(signal.raw_text[:2000])
    description = "\n".join(description_parts)

    severity = payload.severity_override or signal.ai_severity or "medium"
    category = signal.ai_category or "other"

    crisis = Crisis(
        title=title[:255],
        description=description,
        severity=severity,
        status="detected",
        category=category,
    )
    db.add(crisis)
    await db.flush()  # populate crisis.id

    signal.status = SignalStatus.promoted
    signal.crisis_id = crisis.id
    await db.commit()
    await db.refresh(signal)
    return signal
