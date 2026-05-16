from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.crisis import Crisis, CrisisStatus, Severity
from app.models.action_item import ActionItem, ActionItemStatus

router = APIRouter()


@router.get("/")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    # Active crises (not resolved or post_mortem)
    active_stmt = select(func.count()).select_from(Crisis).where(
        Crisis.status not in (CrisisStatus.resolved, CrisisStatus.post_mortem)
    )
    active_result = await db.execute(active_stmt)
    active_crises = active_result.scalar() or 0

    # Actually, use correct SQL:
    stmt_active = select(func.count()).select_from(Crisis).where(
        Crisis.status != "resolved",
        Crisis.status != "post_mortem"
    )
    result_active = await db.execute(stmt_active)
    active_crises = result_active.scalar() or 0

    # Open action items
    stmt_open_actions = select(func.count()).select_from(ActionItem).where(
        ActionItem.status != "completed"
    )
    result_open_actions = await db.execute(stmt_open_actions)
    open_actions = result_open_actions.scalar() or 0

    # Critical crises
    stmt_critical = select(func.count()).select_from(Crisis).where(
        Crisis.severity == "critical"
    )
    result_critical = await db.execute(stmt_critical)
    critical_count = result_critical.scalar() or 0

    # Avg resolution time: crises with resolved_at
    stmt_resolved = select(Crisis).where(Crisis.resolved_at.isnot(None))
    result_resolved = await db.execute(stmt_resolved)
    resolved_crises = result_resolved.scalars().all()
    if resolved_crises:
        total_seconds = sum(
            (c.resolved_at - c.detected_at).total_seconds() for c in resolved_crises
        )
        avg_resolution_hours = round(total_seconds / len(resolved_crises) / 3600, 2)
    else:
        avg_resolution_hours = 0.0

    # Severity breakdown
    stmt_sev = select(Crisis.severity, func.count()).group_by(Crisis.severity)
    result_sev = await db.execute(stmt_sev)
    severity_breakdown = {row[0]: row[1] for row in result_sev.all()}

    # Status breakdown
    stmt_status = select(Crisis.status, func.count()).group_by(Crisis.status)
    result_status = await db.execute(stmt_status)
    status_breakdown = {row[0]: row[1] for row in result_status.all()}

    return {
        "active_crises": active_crises,
        "open_action_items": open_actions,
        "critical_crises": critical_count,
        "avg_resolution_hours": avg_resolution_hours,
        "severity_breakdown": severity_breakdown,
        "status_breakdown": status_breakdown,
        "total_crises": len(resolved_crises) + active_crises,
    }
