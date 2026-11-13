from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score_id: UUID
    scan_id: UUID
    programmer_id: UUID
    documentation_score: Optional[float]
    code_quality_score: Optional[float] = None
    breakdown: Dict[str, Any]


class ProgrammerScoreHistory(BaseModel):
    programmer_id: UUID
    name: str
    email: str
    latest_score: Optional[float] = None
    scans_count: int = 0
    scores: List[ScoreOut] = []


class TeamScoreOut(BaseModel):
    team_id: UUID
    team_name: str
    average_documentation_score: Optional[float]
    programmers_count: int
    ranked_programmers: List[Dict[str, Any]]


class ProjectScoreOut(BaseModel):
    project_id: UUID
    project_name: str
    average_project_score: Optional[float]
    teams_count: int
    ranked_teams: List[Dict[str, Any]]
