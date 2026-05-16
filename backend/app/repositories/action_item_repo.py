from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_item import ActionItem, ActionItemStatus
from app.repositories.base_repo import BaseRepository


class ActionItemRepository(BaseRepository[ActionItem]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ActionItem)

    async def list_by_crisis(self, crisis_id: str, limit: int = 50, offset: int = 0) -> tuple[list[ActionItem], int]:
        stmt = (
            select(ActionItem)
            .where(ActionItem.crisis_id == crisis_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_stmt = select(func.count()).select_from(ActionItem).where(ActionItem.crisis_id == crisis_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        return items, total

    async def list_by_assignee(self, assignee_id: str, limit: int = 50, offset: int = 0) -> tuple[list[ActionItem], int]:
        stmt = (
            select(ActionItem)
            .where(ActionItem.assignee_id == assignee_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_stmt = select(func.count()).select_from(ActionItem).where(ActionItem.assignee_id == assignee_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        return items, total

    async def list_overdue(self, limit: int = 50, offset: int = 0) -> tuple[list[ActionItem], int]:
        now = datetime.utcnow()
        stmt = (
            select(ActionItem)
            .where(
                ActionItem.due_at < now,
                ActionItem.status != ActionItemStatus.completed,
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_stmt = select(func.count()).select_from(ActionItem).where(
            ActionItem.due_at < now,
            ActionItem.status != ActionItemStatus.completed,
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        return items, total
