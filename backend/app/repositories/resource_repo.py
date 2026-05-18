from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource, ResourceStatus, ResourceType
from app.repositories.base_repo import BaseRepository


class ResourceRepository(BaseRepository[Resource]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Resource)

    async def list_by_status(self, status: ResourceStatus, limit: int = 100, offset: int = 0):
        stmt = (
            select(Resource)
            .where(Resource.status == status)
            .order_by(Resource.name)
            .limit(limit)
            .offset(offset)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_available(self, limit: int = 200, offset: int = 0):
        return await self.list_by_status(ResourceStatus.available, limit, offset)

    async def list_by_type(self, t: ResourceType, limit: int = 100, offset: int = 0):
        stmt = select(Resource).where(Resource.resource_type == t).limit(limit).offset(offset)
        return list((await self.db.execute(stmt)).scalars().all())
