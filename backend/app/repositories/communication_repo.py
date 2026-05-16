from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import Communication
from app.repositories.base_repo import BaseRepository


class CommunicationRepository(BaseRepository[Communication]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Communication)

    async def list_by_crisis(self, crisis_id: str, limit: int = 50, offset: int = 0) -> tuple[list[Communication], int]:
        stmt = (
            select(Communication)
            .where(Communication.crisis_id == crisis_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_stmt = select(func.count()).select_from(Communication).where(Communication.crisis_id == crisis_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        return items, total
