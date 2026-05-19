from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_mention import MediaMention
from app.repositories.base_repo import BaseRepository


class MediaMentionRepository(BaseRepository[MediaMention]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, MediaMention)

    async def list_by_crisis(self, crisis_id: str, limit: int = 100, offset: int = 0):
        stmt = (
            select(MediaMention)
            .where(MediaMention.crisis_id == crisis_id)
            .order_by(MediaMention.mentioned_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.db.execute(stmt)).scalars().all())
