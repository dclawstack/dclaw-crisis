import logging
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.utils import utc_now
from app.models.media_mention import MediaMention
from app.schemas.media_mention import (
    MediaMentionCreate,
    MediaMentionResponse,
    MediaMentionUpdate,
)
from app.repositories.media_mention_repo import MediaMentionRepository
from app.services.ai_media_sentiment import analyze_mention
from app.services.llm import LLMUnavailableError

logger = logging.getLogger(__name__)
router = APIRouter()


async def _apply_analysis(m: MediaMention, db: AsyncSession) -> None:
    try:
        result = await analyze_mention(m)
    except LLMUnavailableError as exc:
        logger.warning("media analysis unavailable for %s: %s", m.id, exc)
        return
    except Exception as exc:  # noqa: BLE001
        logger.warning("media analysis failed (%s): %s", type(exc).__name__, exc)
        return
    m.sentiment = result["sentiment"]
    m.sentiment_score = result["sentiment_score"]
    m.key_themes = result["key_themes"]
    m.analyzed_at = utc_now()
    await db.commit()
    await db.refresh(m)


@router.get("/", response_model=list[MediaMentionResponse])
async def list_mentions(
    crisis_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = MediaMentionRepository(db)
    if crisis_id:
        return await repo.list_by_crisis(crisis_id, limit, offset)
    items, _ = await repo.list_all(limit, offset)
    return items


@router.post("/", response_model=MediaMentionResponse, status_code=201)
async def create_mention(payload: MediaMentionCreate, db: AsyncSession = Depends(get_db)):
    mention = MediaMention(
        outlet=payload.outlet,
        url=payload.url,
        headline=payload.headline,
        snippet=payload.snippet,
        author=payload.author,
        crisis_id=payload.crisis_id,
        mentioned_at=payload.mentioned_at or utc_now(),
    )
    repo = MediaMentionRepository(db)
    mention = await repo.create(mention)
    if payload.auto_analyze:
        await _apply_analysis(mention, db)
    return mention


@router.get("/{mention_id}", response_model=MediaMentionResponse)
async def get_mention(mention_id: str, db: AsyncSession = Depends(get_db)):
    m = await MediaMentionRepository(db).get_by_id(mention_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mention not found")
    return m


@router.put("/{mention_id}", response_model=MediaMentionResponse)
async def update_mention(mention_id: str, payload: MediaMentionUpdate, db: AsyncSession = Depends(get_db)):
    repo = MediaMentionRepository(db)
    m = await repo.get_by_id(mention_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mention not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    await db.commit()
    await db.refresh(m)
    return m


@router.post("/{mention_id}/analyze", response_model=MediaMentionResponse)
async def analyze_mention_endpoint(mention_id: str, db: AsyncSession = Depends(get_db)):
    repo = MediaMentionRepository(db)
    m = await repo.get_by_id(mention_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mention not found")
    try:
        result = await analyze_mention(m)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    m.sentiment = result["sentiment"]
    m.sentiment_score = result["sentiment_score"]
    m.key_themes = result["key_themes"]
    m.analyzed_at = utc_now()
    await db.commit()
    await db.refresh(m)
    return m


@router.delete("/{mention_id}", status_code=204)
async def delete_mention(mention_id: str, db: AsyncSession = Depends(get_db)):
    repo = MediaMentionRepository(db)
    m = await repo.get_by_id(mention_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mention not found")
    await repo.delete(m)


class CoverageCounts(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    mixed: int = 0


class MediaCoverageResponse(BaseModel):
    crisis_id: str
    total_mentions: int
    analyzed_count: int
    counts: CoverageCounts
    average_score: float | None
    top_themes: list[str]
    by_outlet: dict[str, int]
    mentions: list[MediaMentionResponse]


@router.get("/coverage/{crisis_id}", response_model=MediaCoverageResponse)
async def crisis_coverage(crisis_id: str, db: AsyncSession = Depends(get_db)):
    mentions = await MediaMentionRepository(db).list_by_crisis(crisis_id, limit=500)
    analyzed = [m for m in mentions if m.sentiment is not None]

    counts = CoverageCounts()
    by_outlet: Counter[str] = Counter()
    theme_counter: Counter[str] = Counter()
    for m in analyzed:
        setattr(counts, m.sentiment, getattr(counts, m.sentiment) + 1)
        theme_counter.update(m.key_themes or [])
    for m in mentions:
        by_outlet[m.outlet] += 1

    avg = (sum(m.sentiment_score or 0 for m in analyzed) / len(analyzed)) if analyzed else None
    top_themes = [t for t, _ in theme_counter.most_common(10)]

    return MediaCoverageResponse(
        crisis_id=crisis_id,
        total_mentions=len(mentions),
        analyzed_count=len(analyzed),
        counts=counts,
        average_score=avg,
        top_themes=top_themes,
        by_outlet=dict(by_outlet),
        mentions=mentions,
    )
