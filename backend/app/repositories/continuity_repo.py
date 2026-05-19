from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.continuity_activation import ContinuityActivation
from app.repositories.base_repo import BaseRepository


class ContinuityActivationRepository(BaseRepository[ContinuityActivation]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ContinuityActivation)

    async def list_by_crisis(self, crisis_id: str):
        stmt = (
            select(ContinuityActivation)
            .where(ContinuityActivation.crisis_id == crisis_id)
            .order_by(ContinuityActivation.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())
