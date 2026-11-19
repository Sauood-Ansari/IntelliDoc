"""Project and team setup, plus authenticated metadata for upload selectors."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.names import name_key
from app.database import get_db
from app.dependencies import get_current_user, allow_project_lead, allow_team_lead
from app.models import Project, Team, ProjectAccessRequest, TeamMembership, AccessStatus, MembershipStatus, UserRole
from app.access import require_project_access
from app.schemas.user import ProjectCreate, ProjectOut, TeamCreate, TeamOut

router = APIRouter(tags=["Projects and teams"])


def search_names(query, model, id_column, search):
    if not search:
        return query
    match = model.name_key.contains(name_key(search), autoescape=True)
    try:
        match = or_(match, id_column == UUID(search.strip()))
    except ValueError:
        pass
    return query.filter(match)


def save_unique(db, record, label):
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, f"That {label} name already exists. Choose a unique name.")
    db.refresh(record)
    return record


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, user=Depends(allow_project_lead), db: Session = Depends(get_db)):
    return save_unique(db, Project(project_name=body.project_name, project_lead_id=user.user_id), "project")


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(user=Depends(get_current_user), db: Session = Depends(get_db),
                  owned: bool = False, eligible: bool = False, search: str = Query("", max_length=150),
                  offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    query = db.query(Project)
    if owned:
        query = query.filter(Project.project_lead_id == user.user_id)
    if eligible:
        if user.role == UserRole.TEAM_LEAD:
            query = query.filter(Project.project_id.in_(db.query(ProjectAccessRequest.project_id).filter_by(
                team_lead_id=user.user_id, status=AccessStatus.APPROVED)))
        elif user.role == UserRole.PROGRAMMER:
            query = query.filter(Project.project_id.in_(db.query(Team.project_id).join(TeamMembership).filter(
                TeamMembership.programmer_id == user.user_id, TeamMembership.status == MembershipStatus.APPROVED)))
        else:
            query = query.filter(Project.project_lead_id == user.user_id)
    query = search_names(query, Project, Project.project_id, search)
    return query.order_by(Project.name_key, Project.project_id).offset(offset).limit(limit).all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def project_detail(project_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/teams", response_model=TeamOut, status_code=201)
def create_team(body: TeamCreate, user=Depends(allow_team_lead), db: Session = Depends(get_db)):
    if db.get(Project, body.project_id) is None:
        raise HTTPException(404, "Create or select an existing project first")
    require_project_access(db, user, body.project_id)
    return save_unique(db, Team(team_name=body.team_name, team_lead_id=user.user_id,
                                project_id=body.project_id), "team")


@router.get("/teams", response_model=list[TeamOut])
def list_teams(user=Depends(get_current_user), db: Session = Depends(get_db),
               project_id: UUID | None = None, owned: bool = False, eligible: bool = False,
               search: str = Query("", max_length=100),
               offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    query = db.query(Team).options(selectinload(Team.project))
    if owned:
        query = query.filter(Team.team_lead_id == user.user_id)
    if eligible:
        if user.role == UserRole.PROGRAMMER:
            query = query.filter(Team.team_id.in_(db.query(TeamMembership.team_id).filter_by(
                programmer_id=user.user_id, status=MembershipStatus.APPROVED)))
        elif user.role == UserRole.TEAM_LEAD:
            query = query.filter(Team.team_lead_id == user.user_id)
        else:
            query = query.join(Project).filter(Project.project_lead_id == user.user_id)
    if project_id is not None:
        query = query.filter(Team.project_id == project_id)
    query = search_names(query, Team, Team.team_id, search)
    return query.order_by(Team.name_key, Team.team_id).offset(offset).limit(limit).all()


@router.get("/teams/{team_id}", response_model=TeamOut)
def team_detail(team_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")
    return team
