from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal, SignalStatus
from app.repositories.base_repo import BaseRepository


class SignalRepository(BaseRepository[Signal]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Signal)

    async def list_by_status(
        self, status: SignalStatus, limit: int = 50, offset: int = 0
    ) -> tuple[list[Signal], int]:
        stmt = (
            select(Signal)
            .where(Signal.status == status)
            .order_by(Signal.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        count_stmt = select(Signal).where(Signal.status == status)
        count_result = await self.db.execute(count_stmt)
        total = len(list(count_result.scalars().all()))
        return items, total

    async def list_unscored(self, limit: int = 50) -> list[Signal]:
        stmt = (
            select(Signal)
            .where(Signal.ai_severity.is_(None))
            .order_by(Signal.detected_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
