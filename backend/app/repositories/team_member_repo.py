from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_member import TeamMember
from app.repositories.base_repo import BaseRepository


class TeamMemberRepository(BaseRepository[TeamMember]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TeamMember)
