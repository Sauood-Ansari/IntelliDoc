from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.score import Score
from app.models.scan import Scan
from app.models.user import User, UserRole, Team, Project
from app.schemas.score import ScoreOut, ProgrammerScoreHistory, TeamScoreOut, ProjectScoreOut
from app.dependencies import (
    get_current_user,
    allow_programmer,
    allow_team_lead,
    allow_project_lead
)
from app.services.scoring_service import ScoringService

router = APIRouter(tags=["Scores & Dashboards"])


@router.get("/scores/me", response_model=ProgrammerScoreHistory)
def get_programmer_scores(
    current_user: User = Depends(allow_programmer),
    db: Session = Depends(get_db)
):
    """
    Programmer metrics, latest score, and historical scores (SRS FR-PROG-001, App B).
    Restricted to authenticated Programmer viewing their own record.
    """
    scores = (
        db.query(Score)
        .filter(Score.programmer_id == current_user.user_id)
        .join(Scan)
        .order_by(Scan.timestamp.desc())
        .all()
    )

    latest = scores[0].documentation_score if scores else None

    return ProgrammerScoreHistory(
        programmer_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        latest_score=latest,
        scans_count=len(scores),
        scores=scores
    )


@router.get("/team/scores", response_model=TeamScoreOut)
def get_team_scores(
    team_id: UUID | None = None,
    current_user: User = Depends(allow_team_lead),
    db: Session = Depends(get_db)
):
    """
    Team Lead dashboard: ranked list of team programmers by score (SRS FR-TEAM-001, Table 3.9, App B).
    Restricted to Team Lead viewing their assigned team.
    """
    # Find the team led by current_user
    query = db.query(Team).filter(Team.team_lead_id == current_user.user_id)
    if team_id is not None:
        query = query.filter(Team.team_id == team_id)
    team = query.order_by(Team.team_id).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No team assigned to this Team Lead."
        )

    team_data = ScoringService.aggregate_team_scores(db, team.team_id)
    return TeamScoreOut(
        team_id=UUID(team_data["team_id"]),
        team_name=team_data["team_name"],
        average_documentation_score=team_data["average_documentation_score"],
        programmers_count=team_data["programmers_count"],
        ranked_programmers=team_data["ranked_programmers"]
    )


@router.get("/project/scores", response_model=ProjectScoreOut)
def get_project_scores(
    project_id: UUID | None = None,
    current_user: User = Depends(allow_project_lead),
    db: Session = Depends(get_db)
):
    """
    Project Lead dashboard: ranked list of teams by aggregated score (SRS FR-PROJ-001, Table 3.9, App B).
    Restricted to Project Lead viewing project aggregations.
    """
    # Find the project led by current_user
    query = db.query(Project).filter(Project.project_lead_id == current_user.user_id)
    if project_id is not None:
        query = query.filter(Project.project_id == project_id)
    project = query.order_by(Project.project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No project assigned to this Project Lead."
        )

    project_data = ScoringService.aggregate_project_scores(db, project.project_id)
    return ProjectScoreOut(
        project_id=UUID(project_data["project_id"]),
        project_name=project_data["project_name"],
        average_project_score=project_data["average_project_score"],
        teams_count=project_data["teams_count"],
        ranked_teams=project_data["ranked_teams"],
        ranked_programmers=project_data["ranked_programmers"]
    )

