from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CodebaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    project_id: Optional[UUID] = None


class CodebaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codebase_id: UUID
    name: str = Field(min_length=1, max_length=150)
    owner_id: UUID
    project_id: Optional[UUID] = None
