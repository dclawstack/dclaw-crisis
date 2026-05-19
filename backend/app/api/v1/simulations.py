import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.utils import utc_now
from app.models.simulation import Simulation, SimulationStatus
from app.schemas.simulation import (
    SimulationCreate,
    SimulationResponse,
    RespondRequest,
    EvaluateResponse,
)
from app.repositories.simulation_repo import SimulationRepository
from app.services.ai_scenario_generator import generate_scenario
from app.services.ai_simulation_evaluator import evaluate_simulation
from app.services.llm import LLMUnavailableError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[SimulationResponse])
async def list_simulations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    items, _ = await SimulationRepository(db).list_all(limit, offset)
    return items


@router.post("/", response_model=SimulationResponse, status_code=201)
async def create_simulation(payload: SimulationCreate, db: AsyncSession = Depends(get_db)):
    sim = Simulation(
        name=payload.name,
        scenario_type=payload.scenario_type,
        severity=payload.severity,
        participants=payload.participants,
        status=SimulationStatus.draft,
    )
    repo = SimulationRepository(db)
    sim = await repo.create(sim)

    if payload.auto_generate:
        try:
            generated = await generate_scenario(payload.scenario_type, payload.severity)
            sim.generated_scenario = generated["scenario"]
            sim.generated_actions = generated["expected_actions"]
            sim.expected_outcomes = generated["expected_outcomes"]
            await db.commit()
            await db.refresh(sim)
        except LLMUnavailableError as exc:
            logger.warning("scenario generation LLM unavailable: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("scenario generation failed (%s): %s", type(exc).__name__, exc)
    return sim


@router.get("/{sim_id}", response_model=SimulationResponse)
async def get_simulation(sim_id: str, db: AsyncSession = Depends(get_db)):
    sim = await SimulationRepository(db).get_by_id(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


@router.delete("/{sim_id}", status_code=204)
async def delete_simulation(sim_id: str, db: AsyncSession = Depends(get_db)):
    repo = SimulationRepository(db)
    sim = await repo.get_by_id(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    await repo.delete(sim)


@router.post("/{sim_id}/start", response_model=SimulationResponse)
async def start_simulation(sim_id: str, db: AsyncSession = Depends(get_db)):
    repo = SimulationRepository(db)
    sim = await repo.get_by_id(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim.status != SimulationStatus.draft.value:
        raise HTTPException(status_code=400, detail=f"Cannot start a simulation in status {sim.status}")
    sim.status = SimulationStatus.running
    sim.started_at = utc_now()
    await db.commit()
    await db.refresh(sim)
    return sim


@router.post("/{sim_id}/respond", response_model=SimulationResponse)
async def respond_simulation(sim_id: str, payload: RespondRequest, db: AsyncSession = Depends(get_db)):
    repo = SimulationRepository(db)
    sim = await repo.get_by_id(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim.status not in (SimulationStatus.running.value, SimulationStatus.draft.value):
        raise HTTPException(status_code=400, detail="Cannot record response on a completed simulation")
    sim.operator_notes = payload.operator_notes
    await db.commit()
    await db.refresh(sim)
    return sim


@router.post("/{sim_id}/evaluate", response_model=EvaluateResponse)
async def evaluate_simulation_endpoint(sim_id: str, db: AsyncSession = Depends(get_db)):
    repo = SimulationRepository(db)
    sim = await repo.get_by_id(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if not sim.operator_notes:
        raise HTTPException(status_code=400, detail="No operator response recorded yet — POST /respond first")
    try:
        result = await evaluate_simulation(sim)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed JSON: {exc}")

    sim.evaluation_summary = result["summary"]
    sim.score = result["score"]
    sim.evaluation_breakdown = result["breakdown"]
    sim.status = SimulationStatus.completed
    sim.completed_at = utc_now()
    await db.commit()
    await db.refresh(sim)
    return EvaluateResponse(**result)
