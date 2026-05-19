from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_hold import LegalHold, LegalHoldStatus
from app.repositories.base_repo import BaseRepository


class LegalHoldRepository(BaseRepository[LegalHold]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, LegalHold)

    async def list_by_crisis(self, crisis_id: str, limit: int = 50, offset: int = 0):
        stmt = (
            select(LegalHold)
            .where(LegalHold.crisis_id == crisis_id)
            .order_by(LegalHold.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_active(self, limit: int = 50, offset: int = 0):
        stmt = (
            select(LegalHold)
            .where(LegalHold.status == LegalHoldStatus.active)
            .order_by(LegalHold.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.db.execute(stmt)).scalars().all())
