from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.models.crisis import Crisis
from app.schemas.crisis import CrisisCreate, CrisisUpdate, CrisisResponse
from app.repositories.crisis_repo import CrisisRepository
from app.services.ai_summarizer import summarize_crisis
from app.services.ai_recommender import recommend_next_action
from app.services.ai_post_mortem import generate_post_mortem
from app.services.ai_playbook_advisor import suggest_playbook_updates
from app.services.ai_stakeholder_prioritizer import prioritize_stakeholders
from app.services.ai_resource_matcher import match_resources
from app.services.ai_legal_hold import draft_hold_notice, recommend_evidence
from app.services.continuity_client import activate_bcp
from app.services.exports import render_post_mortem_markdown
from app.services.llm import LLMUnavailableError
from app.repositories.communication_repo import CommunicationRepository
from app.repositories.continuity_repo import ContinuityActivationRepository
from app.models.continuity_activation import ActivationStatus, ContinuityActivation
from app.schemas.continuity_activation import (
    ActivateBCPRequest,
    ContinuityActivationResponse,
)
from app.core.utils import utc_now
from app.core.object_store import get_object_store
from app.core.rate_limit import hourly_limit

_ai_rl = [Depends(hourly_limit("ai-crisis"))]

router = APIRouter()


@router.get("", response_model=list[CrisisResponse])
async def list_crises(
    status: Literal["detected", "assessing", "responding", "contained", "resolved", "post_mortem"] | None = None,
    severity: Literal["critical", "high", "medium", "low"] | None = None,
    category: Literal["operational", "security", "legal", "pr", "supply_chain", "hr", "financial", "other"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = CrisisRepository(db)
    if status:
        from app.models.crisis import CrisisStatus
        items, _ = await repo.list_by_status(CrisisStatus(status), limit, offset)
    elif severity:
        from app.models.crisis import Severity
        items, _ = await repo.list_by_severity(Severity(severity), limit, offset)
    elif category:
        from app.models.crisis import CrisisCategory
        items, _ = await repo.list_by_category(CrisisCategory(category), limit, offset)
    else:
        items, _ = await repo.list_all(limit, offset)
    return items


@router.post("", response_model=CrisisResponse, status_code=201)
async def create_crisis(payload: CrisisCreate, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    data = payload.model_dump()
    if data.get("detected_at") is None:
        from app.core.utils import utc_now
        data["detected_at"] = utc_now()
    crisis = Crisis(**data)
    return await repo.create(crisis)


@router.get("/{crisis_id}", response_model=CrisisResponse)
async def get_crisis(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_with_actions(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    return crisis


@router.put("/{crisis_id}", response_model=CrisisResponse)
async def update_crisis(crisis_id: str, payload: CrisisUpdate, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(crisis, key, value)
    await db.commit()
    await db.refresh(crisis)
    return crisis


@router.delete("/{crisis_id}", status_code=204)
async def delete_crisis(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    await repo.delete(crisis)


class SummaryResponse(BaseModel):
    summary: str


class NextActionResponse(BaseModel):
    title: str
    description: str
    priority: str
    rationale: str
    suggested_assignee_role: str


@router.post("/{crisis_id}/summarize", response_model=SummaryResponse, dependencies=_ai_rl)
async def summarize(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        text = await summarize_crisis(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return SummaryResponse(summary=text)


@router.get("/{crisis_id}/next-action", response_model=NextActionResponse, dependencies=_ai_rl)
async def next_action(crisis_id: str, db: AsyncSession = Depends(get_db)):
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await recommend_next_action(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return NextActionResponse(**data)


class PostMortemResponse(BaseModel):
    timeline_summary: str
    what_went_well: list[str]
    what_went_poorly: list[str]
    root_cause: str
    lessons_learned: list[str]
    is_speculative: bool


class PlaybookChange(BaseModel):
    kind: str
    step_order: int | None
    new_title: str | None
    new_description: str | None
    new_role: str | None
    rationale: str


class PlaybookAdvisorResponse(BaseModel):
    playbook_id: str | None
    playbook_name: str | None
    summary: str
    suggested_changes: list[PlaybookChange]


@router.post("/{crisis_id}/post-mortem", response_model=PostMortemResponse, dependencies=_ai_rl)
async def post_mortem(crisis_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a structured post-mortem. Works best for resolved/contained crises but accepts any status."""
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await generate_post_mortem(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return PostMortemResponse(**data)


@router.post("/{crisis_id}/suggest-playbook-updates", response_model=PlaybookAdvisorResponse, dependencies=_ai_rl)
async def suggest_playbook_changes(crisis_id: str, db: AsyncSession = Depends(get_db)):
    """Suggest concrete updates to the closest-matching playbook based on this crisis."""
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await suggest_playbook_updates(crisis, db)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return PlaybookAdvisorResponse(**data)


class StakeholderPriority(BaseModel):
    stakeholder_id: str
    stakeholder_name: str
    stakeholder_type: str
    organization: str | None
    urgency: str
    channel: str
    talking_points: list[str]
    rationale: str


class StakeholderPrioritiesResponse(BaseModel):
    priorities: list[StakeholderPriority]
    notes: str


class ResourceRecommendation(BaseModel):
    resource_id: str
    resource_name: str
    resource_type: str
    current_status: str
    fit_score: float
    deploy_now: bool
    reason: str
    conflict_note: str | None


class ResourceRecommendationsResponse(BaseModel):
    recommendations: list[ResourceRecommendation]
    gaps: list[str]


@router.get("/{crisis_id}/stakeholder-priorities", response_model=StakeholderPrioritiesResponse, dependencies=_ai_rl)
async def stakeholder_priorities(crisis_id: str, db: AsyncSession = Depends(get_db)):
    """Rank which stakeholders to contact and how, given the crisis context."""
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await prioritize_stakeholders(crisis, db)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return StakeholderPrioritiesResponse(**data)


@router.get("/{crisis_id}/recommend-resources", response_model=ResourceRecommendationsResponse, dependencies=_ai_rl)
async def recommend_resources(crisis_id: str, db: AsyncSession = Depends(get_db)):
    """Recommend which resources to deploy for this crisis."""
    repo = CrisisRepository(db)
    crisis = await repo.get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await match_resources(crisis, db)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return ResourceRecommendationsResponse(**data)


from datetime import datetime as _datetime  # noqa: E402


class SentimentTrendPoint(BaseModel):
    communication_id: str
    sentiment: str
    sentiment_score: float
    analyzed_at: _datetime
    comm_type: str
    channel: str
    risk_flag_count: int


class SentimentCounts(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    mixed: int = 0


class SentimentTrendResponse(BaseModel):
    crisis_id: str
    analyzed_count: int
    total_communications: int
    counts: SentimentCounts
    average_score: float | None
    trend_direction: str  # "improving" | "worsening" | "flat" | "insufficient_data"
    points: list[SentimentTrendPoint]


def _trend_direction(scores_by_time: list[float]) -> str:
    if len(scores_by_time) < 2:
        return "insufficient_data"
    first_half = scores_by_time[: len(scores_by_time) // 2]
    second_half = scores_by_time[len(scores_by_time) // 2 :]
    if not first_half or not second_half:
        return "insufficient_data"
    delta = (sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half))
    if delta > 0.1:
        return "improving"
    if delta < -0.1:
        return "worsening"
    return "flat"


@router.get("/{crisis_id}/sentiment-trend", response_model=SentimentTrendResponse)
async def sentiment_trend(crisis_id: str, db: AsyncSession = Depends(get_db)):
    """Aggregated sentiment timeline across all analyzed communications for this crisis."""
    crisis = await CrisisRepository(db).get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")

    comm_repo = CommunicationRepository(db)
    all_comms, _ = await comm_repo.list_by_crisis(crisis_id, limit=500, offset=0)
    analyzed = [c for c in all_comms if c.sentiment is not None and c.sentiment_analyzed_at is not None]
    analyzed.sort(key=lambda c: c.sentiment_analyzed_at)

    counts = SentimentCounts()
    points: list[SentimentTrendPoint] = []
    for c in analyzed:
        setattr(counts, c.sentiment, getattr(counts, c.sentiment, 0) + 1)
        points.append(
            SentimentTrendPoint(
                communication_id=c.id,
                sentiment=c.sentiment,
                sentiment_score=c.sentiment_score or 0.0,
                analyzed_at=c.sentiment_analyzed_at,
                comm_type=c.comm_type,
                channel=c.channel,
                risk_flag_count=len(c.risk_flags or []),
            )
        )

    avg = sum(p.sentiment_score for p in points) / len(points) if points else None
    direction = _trend_direction([p.sentiment_score for p in points])

    return SentimentTrendResponse(
        crisis_id=crisis_id,
        analyzed_count=len(points),
        total_communications=len(all_comms),
        counts=counts,
        average_score=avg,
        trend_direction=direction,
        points=points,
    )


# ── P2.2 Continuity activation ───────────────────────────────────────────────


@router.post("/{crisis_id}/activate-bcp", response_model=ContinuityActivationResponse, status_code=201)
async def activate_bcp_endpoint(
    crisis_id: str, payload: ActivateBCPRequest, db: AsyncSession = Depends(get_db)
):
    """Activate a Business Continuity Plan for this crisis via DClaw Continuity.

    Falls back to simulator mode if `CONTINUITY_API_URL` is not configured.
    """
    crisis = await CrisisRepository(db).get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")

    result = await activate_bcp(
        crisis_id=crisis.id,
        crisis_title=crisis.title,
        crisis_severity=crisis.severity,
        crisis_category=crisis.category,
        bcp_plan_id=payload.bcp_plan_id,
        bcp_plan_name=payload.bcp_plan_name,
        notes=payload.notes,
    )

    activation = ContinuityActivation(
        crisis_id=crisis.id,
        bcp_plan_id=payload.bcp_plan_id,
        bcp_plan_name=payload.bcp_plan_name,
        provider=result["provider"],
        status=ActivationStatus(result["status"]) if result["status"] in {s.value for s in ActivationStatus} else ActivationStatus.failed,
        request_payload={"bcp_plan_id": payload.bcp_plan_id, "bcp_plan_name": payload.bcp_plan_name, "notes": payload.notes},
        response_payload=result.get("response_payload") or {},
        error_message=result.get("error_message"),
    )
    if activation.status == ActivationStatus.activated:
        activation.activated_at = utc_now()
    repo = ContinuityActivationRepository(db)
    return await repo.create(activation)


@router.get("/{crisis_id}/activations", response_model=list[ContinuityActivationResponse])
async def list_activations(crisis_id: str, db: AsyncSession = Depends(get_db)):
    crisis = await CrisisRepository(db).get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    return await ContinuityActivationRepository(db).list_by_crisis(crisis_id)


# ── P2.4 Legal Hold AI helpers ────────────────────────────────────────────────


class DraftHoldResponse(BaseModel):
    notice_text: str


class EvidenceDataSource(BaseModel):
    name: str
    type: str
    rationale: str


class EvidenceCustodian(BaseModel):
    role: str
    reason: str


class EvidenceRecommendation(BaseModel):
    data_sources: list[EvidenceDataSource]
    custodians: list[EvidenceCustodian]
    preservation_duration_days_min: int


@router.post("/{crisis_id}/draft-hold-notice", response_model=DraftHoldResponse, dependencies=_ai_rl)
async def draft_hold_notice_endpoint(crisis_id: str, db: AsyncSession = Depends(get_db)):
    crisis = await CrisisRepository(db).get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        text = await draft_hold_notice(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return DraftHoldResponse(notice_text=text)


@router.post("/{crisis_id}/recommend-evidence", response_model=EvidenceRecommendation, dependencies=_ai_rl)
async def recommend_evidence_endpoint(crisis_id: str, db: AsyncSession = Depends(get_db)):
    crisis = await CrisisRepository(db).get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        data = await recommend_evidence(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")
    return EvidenceRecommendation(**data)


class PostMortemExportResponse(BaseModel):
    key: str
    url: str
    backend: str
    size_bytes: int


@router.post(
    "/{crisis_id}/export-post-mortem",
    response_model=PostMortemExportResponse,
    dependencies=_ai_rl,
)
async def export_post_mortem(crisis_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a post-mortem (cached via Redis) and store as markdown."""
    crisis = await CrisisRepository(db).get_by_id(crisis_id)
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    try:
        post_mortem = await generate_post_mortem(crisis)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    md = render_post_mortem_markdown(crisis, post_mortem)
    key = f"crises/{crisis.id}/post-mortem.md"
    store = get_object_store()
    store.put_text(key, md, content_type="text/markdown")
    url = store.presigned_get_url(key)
    return PostMortemExportResponse(
        key=key, url=url, backend=getattr(store, "backend", "unknown"), size_bytes=len(md.encode("utf-8"))
    )
