from sqlalchemy.ext.asyncio import AsyncSession

from app.models.playbook import Playbook
from app.repositories.base_repo import BaseRepository


class PlaybookRepository(BaseRepository[Playbook]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Playbook)
