from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_external_id(self, provider: str, external_id: str) -> User | None:
        stmt = select(User).where(User.auth_provider == provider, User.external_id == external_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()
