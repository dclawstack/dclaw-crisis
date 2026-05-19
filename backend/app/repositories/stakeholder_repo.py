from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stakeholder import Stakeholder, StakeholderType, StakeholderImportance
from app.repositories.base_repo import BaseRepository


class StakeholderRepository(BaseRepository[Stakeholder]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Stakeholder)

    async def list_by_type(self, t: StakeholderType, limit: int = 100, offset: int = 0):
        stmt = select(Stakeholder).where(Stakeholder.type == t).limit(limit).offset(offset)
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_active(self, limit: int = 200, offset: int = 0):
        stmt = (
            select(Stakeholder)
            .where(Stakeholder.is_active.is_(True))
            .order_by(Stakeholder.importance, Stakeholder.name)
            .limit(limit)
            .offset(offset)
        )
        return list((await self.db.execute(stmt)).scalars().all())
