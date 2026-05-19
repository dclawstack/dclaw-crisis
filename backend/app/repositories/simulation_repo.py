from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation import Simulation
from app.repositories.base_repo import BaseRepository


class SimulationRepository(BaseRepository[Simulation]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Simulation)
