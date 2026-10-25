"""IntelliDoc — Dashboard routers for all three role levels."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.models import User, UserRole, Scan, Score, Team, Project
from app.schemas.schemas import (
    ProgrammerMetrics, TeamMetrics, ProjectMetrics, UserOut, TeamOut, ProjectOut, ScoreOut
)

router = APIRouter(prefix="/dashboard", tags=["Dashboards"])


# ─── Programmer Dashboard ─────────────────────────────────────────────────────

@router.get("/me", response_model=ProgrammerMetrics)
def get_programmer_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Programmer's personal metrics and scan history."""
    scores = (
        db.query(Score)
        .filter(Score.programmer_id == current_user.id)
        .order_by(Score.created_at.desc())
        .all()
    )

    latest_score = scores[0].total_score if scores else None
    scan_count = db.query(Scan).filter(Scan.initiated_by == current_user.id).count()
    last_scan = (
        db.query(Scan)
        .filter(Scan.initiated_by == current_user.id)
        .order_by(Scan.created_at.desc())
        .first()
    )

    # Last 10 scores for trend
    trend = [s.total_score for s in scores[:10]][::-1]

    return ProgrammerMetrics(
        user=UserOut.model_validate(current_user),
        latest_score=latest_score,
        scan_count=scan_count,
        last_scan_at=last_scan.created_at if last_scan else None,
        score_trend=trend,
    )


# ─── Team Lead Dashboard ──────────────────────────────────────────────────────

@router.get("/team", response_model=list[TeamMetrics])
def get_team_dashboard(
    current_user: User = Depends(require_role(UserRole.team_lead)),
    db: Session = Depends(get_db),
):
    """Team Lead view: ranked programmers with metrics for each led team."""
    results = []

    for team in current_user.led_teams:
        members = db.query(User).filter(User.team_id == team.id).all()
        programmer_metrics = []

        for member in members:
            scores = (
                db.query(Score)
                .filter(Score.programmer_id == member.id)
                .order_by(Score.created_at.desc())
                .all()
            )
            latest = scores[0].total_score if scores else None
            scan_count = db.query(Scan).filter(Scan.initiated_by == member.id).count()
            last_scan = (
                db.query(Scan)
                .filter(Scan.initiated_by == member.id)
                .order_by(Scan.created_at.desc())
                .first()
            )
            trend = [s.total_score for s in scores[:10]][::-1]

            programmer_metrics.append(ProgrammerMetrics(
                user=UserOut.model_validate(member),
                latest_score=latest,
                scan_count=scan_count,
                last_scan_at=last_scan.created_at if last_scan else None,
                score_trend=trend,
            ))

        # Algorithm 11: Team aggregation (weighted by function count)
        team_score = _compute_team_score(members, db)

        results.append(TeamMetrics(
            team=TeamOut.model_validate(team),
            team_score=team_score,
            programmer_count=len(members),
            programmers=sorted(
                programmer_metrics,
                key=lambda p: p.latest_score if p.latest_score is not None else -1,
                reverse=True,
            ),
        ))

    return results


# ─── Project Lead Dashboard ───────────────────────────────────────────────────

@router.get("/project", response_model=list[ProjectMetrics])
def get_project_dashboard(
    current_user: User = Depends(require_role(UserRole.project_lead)),
    db: Session = Depends(get_db),
):
    """Project Lead view: cross-team aggregated metrics."""
    projects = db.query(Project).filter(Project.project_lead_id == current_user.id).all()
    results = []

    for project in projects:
        teams = db.query(Team).filter(Team.project_id == project.id).all()
        team_metrics = []

        for team in teams:
            members = db.query(User).filter(User.team_id == team.id).all()
            programmer_metrics = []

            for member in members:
                scores = (
                    db.query(Score)
                    .filter(Score.programmer_id == member.id)
                    .order_by(Score.created_at.desc())
                    .all()
                )
                latest = scores[0].total_score if scores else None
                scan_count = db.query(Scan).filter(Scan.initiated_by == member.id).count()
                last_scan = (
                    db.query(Scan)
                    .filter(Scan.initiated_by == member.id)
                    .order_by(Scan.created_at.desc())
                    .first()
                )
                programmer_metrics.append(ProgrammerMetrics(
                    user=UserOut.model_validate(member),
                    latest_score=latest,
                    scan_count=scan_count,
                    last_scan_at=last_scan.created_at if last_scan else None,
                ))

            team_score = _compute_team_score(members, db)
            team_metrics.append(TeamMetrics(
                team=TeamOut.model_validate(team),
                team_score=team_score,
                programmer_count=len(members),
                programmers=programmer_metrics,
            ))

        # Algorithm 12: Project aggregation (mean of team scores)
        valid_team_scores = [t.team_score for t in team_metrics if t.team_score is not None]
        project_score = sum(valid_team_scores) / len(valid_team_scores) if valid_team_scores else None

        results.append(ProjectMetrics(
            project=ProjectOut.model_validate(project),
            project_score=project_score,
            team_count=len(teams),
            teams=sorted(
                team_metrics,
                key=lambda t: t.team_score if t.team_score is not None else -1,
                reverse=True,
            ),
        ))

    return results


# ─── Helper ────────────────────────────────────────────────────────────────────

def _compute_team_score(members: list[User], db: Session) -> Optional[float]:
    """Algorithm 11: weighted team score by function count."""
    weighted_sum = 0.0
    total_weight = 0

    for member in members:
        latest_score = (
            db.query(Score)
            .filter(Score.programmer_id == member.id)
            .order_by(Score.created_at.desc())
            .first()
        )
        if latest_score:
            latest_scan = db.query(Scan).filter(Scan.id == latest_score.scan_id).first()
            weight = latest_scan.total_functions if latest_scan else 1
            weighted_sum += latest_score.total_score * weight
            total_weight += weight

    if total_weight == 0:
        return None
    return round(weighted_sum / total_weight, 2)
