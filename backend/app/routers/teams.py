"""IntelliDoc — Teams and Projects router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.models import User, UserRole, Team, Project
from app.schemas.schemas import TeamCreate, TeamOut, ProjectCreate, ProjectOut

router = APIRouter(tags=["Teams & Projects"])


# ─── Teams ────────────────────────────────────────────────────────────────────

@router.post("/teams", response_model=TeamOut, status_code=201)
def create_team(
    body: TeamCreate,
    current_user: User = Depends(require_role(UserRole.team_lead, UserRole.project_lead)),
    db: Session = Depends(get_db),
):
    team = Team(name=body.name, project_id=body.project_id, team_lead_id=current_user.id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return TeamOut.model_validate(team)


@router.get("/teams", response_model=list[TeamOut])
def list_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.project_lead:
        teams = db.query(Team).all()
    elif current_user.role == UserRole.team_lead:
        teams = current_user.led_teams
    else:
        teams = [current_user.team] if current_user.team else []
    return [TeamOut.model_validate(t) for t in teams]


@router.patch("/teams/{team_id}/members/{user_id}")
def add_team_member(
    team_id: str,
    user_id: str,
    current_user: User = Depends(require_role(UserRole.team_lead, UserRole.project_lead)),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.team_lead_id != current_user.id and current_user.role != UserRole.project_lead:
        raise HTTPException(status_code=403, detail="Not your team")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.team_id = team_id
    db.commit()
    return {"message": f"User {user.name} added to team {team.name}"}


# ─── Projects ─────────────────────────────────────────────────────────────────

@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    body: ProjectCreate,
    current_user: User = Depends(require_role(UserRole.project_lead)),
    db: Session = Depends(get_db),
):
    project = Project(
        name=body.name,
        description=body.description,
        project_lead_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    current_user: User = Depends(require_role(UserRole.project_lead)),
    db: Session = Depends(get_db),
):
    projects = db.query(Project).filter(Project.project_lead_id == current_user.id).all()
    return [ProjectOut.model_validate(p) for p in projects]


# ─── Users management ─────────────────────────────────────────────────────────

@router.get("/users", response_model=list)
def list_users(
    current_user: User = Depends(require_role(UserRole.team_lead, UserRole.project_lead)),
    db: Session = Depends(get_db),
):
    """List users for management (leads only)."""
    from app.schemas.schemas import UserOut
    if current_user.role == UserRole.project_lead:
        users = db.query(User).all()
    else:
        # Team leads see their team members + unassigned programmers
        team_ids = [t.id for t in current_user.led_teams]
        users = db.query(User).filter(
            (User.team_id.in_(team_ids)) | (User.team_id.is_(None))
        ).all()
    return [UserOut.model_validate(u) for u in users]
