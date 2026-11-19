from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.models.user import UserRole
from app.core.names import clean_name
from pydantic import field_validator


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: UserRole
    team_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(min_length=10, max_length=72)

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        value = clean_name(value)
        if not value or len(value) > 100:
            raise ValueError("Use a name between 1 and 100 characters")
        return value


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    created_at: datetime


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    team_id: UUID
    team_name: str
    team_lead_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: UUID
    project_name: str
    project_lead_id: UUID


class ProjectCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=150)

    @field_validator("project_name")
    @classmethod
    def check_name(cls, value):
        value = clean_name(value)
        if not value or len(value) > 150:
            raise ValueError("Use a project name between 1 and 150 characters")
        return value


class TeamCreate(BaseModel):
    team_name: str = Field(min_length=1, max_length=100)
    project_id: UUID

    @field_validator("team_name")
    @classmethod
    def check_name(cls, value):
        value = clean_name(value)
        if not value or len(value) > 100:
            raise ValueError("Use a team name between 1 and 100 characters")
        return value
