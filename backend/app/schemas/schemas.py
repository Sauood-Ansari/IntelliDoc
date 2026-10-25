"""IntelliDoc — Pydantic request/response schemas."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# ─── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = "programmer"
    team_id: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = {"programmer", "team_lead", "project_lead"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── Users ────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    team_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Teams & Projects ─────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    project_id: Optional[str] = None


class TeamOut(BaseModel):
    id: str
    name: str
    project_id: Optional[str] = None
    team_lead_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_lead_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Scans ────────────────────────────────────────────────────────────────────

class ScanOut(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_files: int
    parsed_files: int
    failed_files: int
    total_functions: int
    documented_functions: int
    initiated_by: str
    score: Optional["ScoreOut"] = None

    model_config = {"from_attributes": True}


class ScanListItem(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    total_functions: int
    documented_functions: int
    score_value: Optional[float] = None

    model_config = {"from_attributes": True}


# ─── Findings ─────────────────────────────────────────────────────────────────

class FindingOut(BaseModel):
    id: str
    finding_type: str
    severity: str
    explanation: str
    extra: dict
    function_id: str
    function_name: Optional[str] = None
    function_line: Optional[int] = None
    file_path: Optional[str] = None

    model_config = {"from_attributes": True}


class FindingPage(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[FindingOut]


# ─── Functions ────────────────────────────────────────────────────────────────

class FunctionOut(BaseModel):
    id: str
    name: str
    line_number: int
    signature: Optional[str] = None
    has_docstring: bool
    docstring: Optional[str] = None
    params: list[str]
    has_return_statement: bool
    file_path: Optional[str] = None
    findings: list[FindingOut] = []
    ai_analyses: list["AIAnalysisOut"] = []

    model_config = {"from_attributes": True}


# ─── AI Analyses ──────────────────────────────────────────────────────────────

class AIAnalysisOut(BaseModel):
    id: str
    analysis_type: str
    provider: str
    status: str
    result: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIGenerateRequest(BaseModel):
    pass  # No body needed; function context comes from DB


class AIConsistencyRequest(BaseModel):
    pass  # No body needed; function context comes from DB


# ─── Scores ───────────────────────────────────────────────────────────────────

class ScoreOut(BaseModel):
    id: str
    total_score: float
    completeness_score: float
    param_consistency_score: float
    return_consistency_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Dashboard ────────────────────────────────────────────────────────────────

class ProgrammerMetrics(BaseModel):
    user: UserOut
    latest_score: Optional[float] = None
    scan_count: int
    last_scan_at: Optional[datetime] = None
    score_trend: list[float] = []


class TeamMetrics(BaseModel):
    team: TeamOut
    team_score: Optional[float] = None
    programmer_count: int
    programmers: list[ProgrammerMetrics]


class ProjectMetrics(BaseModel):
    project: ProjectOut
    project_score: Optional[float] = None
    team_count: int
    teams: list[TeamMetrics]


# Forward reference resolution
TokenResponse.model_rebuild()
ScanOut.model_rebuild()
FunctionOut.model_rebuild()
