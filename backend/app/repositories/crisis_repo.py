from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crisis import Crisis, CrisisStatus, Severity, CrisisCategory
from app.repositories.base_repo import BaseRepository


class CrisisRepository(BaseRepository[Crisis]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Crisis)

    async def list_by_status(self, status: CrisisStatus, limit: int = 20, offset: int = 0) -> tuple[list[Crisis], int]:
        stmt = select(Crisis).where(Crisis.status == status).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_result = await self.db.execute(
            select(Crisis).where(Crisis.status == status)
        )
        total = len(list(count_result.scalars().all()))
        return items, total

    async def list_by_severity(self, severity: Severity, limit: int = 20, offset: int = 0) -> tuple[list[Crisis], int]:
        stmt = select(Crisis).where(Crisis.severity == severity).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_result = await self.db.execute(
            select(Crisis).where(Crisis.severity == severity)
        )
        total = len(list(count_result.scalars().all()))
        return items, total

    async def list_by_category(self, category: CrisisCategory, limit: int = 20, offset: int = 0) -> tuple[list[Crisis], int]:
        stmt = select(Crisis).where(Crisis.category == category).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_result = await self.db.execute(
            select(Crisis).where(Crisis.category == category)
        )
        total = len(list(count_result.scalars().all()))
        return items, total

    async def get_with_actions(self, crisis_id: str) -> Crisis | None:
        return await self.get_by_id(crisis_id)
