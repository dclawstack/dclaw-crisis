"""Public demo seed/reset endpoints for the landing-page demo flow.

These endpoints are deliberately UNAUTHENTICATED so a landing-page visitor
who hasn't signed up can populate sample data and sign in *as the demo
user* (created during seed).

Gated by `ENABLE_DEMO_MODE`:
- Off (production default) → `/status` returns 200 with `enabled:false`
  (so the frontend can probe and quietly hide the section); `/seed` and
  `/reset` return 403.
- On (local dev) → all three endpoints work.

Demo records carry unambiguous markers (DEMO: prefix on titles/names,
demo: on signal sources, DEMO on media outlets, and the single email
`settings.demo_user_email`). `/reset` deletes only those — real operator
data is never touched.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.demo_seed import (
    demo_credentials,
    get_demo_counts,
    is_seeded,
    reset_demo,
    seed_demo,
)

router = APIRouter()


def _ensure_enabled() -> None:
    if not settings.enable_demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode is disabled. Set ENABLE_DEMO_MODE=true to enable.",
        )


@router.get("/status")
async def status_endpoint(db: AsyncSession = Depends(get_db)):
    """Public — returns enabled flag so the frontend can quietly auto-hide.

    Always 200. When the flag is off, `seeded` and `counts` come back as
    falsy / zeros without touching the database — but we still hit the DB
    on success to give live counts so the UI can confirm what's loaded.
    """
    if not settings.enable_demo_mode:
        return {
            "enabled": False,
            "seeded": False,
            "counts": {
                "crises": 0, "team_members": 0, "stakeholders": 0, "resources": 0,
                "signals": 0, "simulations": 0, "legal_holds": 0, "media_mentions": 0,
            },
        }
    counts = await get_demo_counts(db)
    return {
        "enabled": True,
        "seeded": any(v > 0 for v in counts.values()),
        "counts": counts,
    }


@router.post("/seed")
async def seed_endpoint(db: AsyncSession = Depends(get_db)):
    """Public — populate demo dataset + return the demo user's credentials.

    Idempotent: re-running returns existing counts and the same credentials.
    """
    _ensure_enabled()
    result = await seed_demo(db)
    counts = await get_demo_counts(db)
    return {
        "enabled": True,
        "seeded": any(v > 0 for v in counts.values()),
        "counts": counts,
        "result": result,
        "demo_credentials": demo_credentials(),
    }


@router.delete("/reset")
async def reset_endpoint(db: AsyncSession = Depends(get_db)):
    """Public — remove every demo-marked row + the demo user. Real data untouched."""
    _ensure_enabled()
    deleted = await reset_demo(db)
    counts = await get_demo_counts(db)
    return {
        "enabled": True,
        "seeded": False,
        "counts": counts,
        "deleted": deleted,
    }
