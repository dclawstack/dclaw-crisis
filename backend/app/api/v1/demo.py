"""Demo seed/clear endpoints for the landing-page demo flow."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.demo_seed import clear_demo, get_demo_counts, is_seeded, seed_demo

router = APIRouter()


@router.get("/status")
async def status(db: AsyncSession = Depends(get_db)):
    counts = await get_demo_counts(db)
    return {"seeded": any(v > 0 for v in counts.values()), "counts": counts}


@router.post("/seed")
async def seed(db: AsyncSession = Depends(get_db)):
    """Insert demo dataset. No-op if demo data already exists."""
    return await seed_demo(db)


@router.post("/clear")
async def clear(db: AsyncSession = Depends(get_db)):
    """Remove every demo-prefixed row. Real data is untouched."""
    return await clear_demo(db)
