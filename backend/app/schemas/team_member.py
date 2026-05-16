from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class TeamMemberBase(BaseModel):
    name: str
    email: str
    role: str
    department: str | None = None
    phone: str | None = None
    is_active: bool = True


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    department: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class TeamMemberResponse(TeamMemberBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
