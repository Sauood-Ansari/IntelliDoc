from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.models.user import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: UserRole
    team_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(min_length=10, max_length=72)


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    created_at: datetime


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    team_id: UUID
    team_name: str
    team_lead_id: Optional[UUID] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: UUID
    project_name: str
    project_lead_id: UUID
