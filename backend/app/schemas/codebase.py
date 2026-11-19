from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.names import clean_name


class CodebaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    project_id: UUID
    team_id: UUID

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        value = clean_name(value)
        if not value or len(value) > 150:
            raise ValueError("Enter a codebase name between 1 and 150 characters")
        return value


class CodebaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codebase_id: UUID
    name: str = Field(min_length=1, max_length=150)
    owner_id: UUID
    project_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    project_name: Optional[str] = None
    team_name: Optional[str] = None
