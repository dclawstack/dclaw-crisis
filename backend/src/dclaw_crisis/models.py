from pydantic import BaseModel
from datetime import datetime
from typing import List

class CrisisPlan(BaseModel):
    id: str
    scenario: str
    severity_level: str
    response_team: list[str]
    communication_channels: list[str]
    eta_resolution_hours: int
    created_at: datetime

class CrisisCreate(BaseModel):
    scenario: str
