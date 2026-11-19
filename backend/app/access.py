"""Shared scope for every resource endpoint."""
from fastapi import HTTPException
from sqlalchemy import and_, or_
from app.models import Codebase, Scan, User, Team, Project, UserRole, ProjectAccessRequest, TeamMembership, AccessStatus, MembershipStatus

def codebases_for(db, user):
    query = db.query(Codebase)
    if user.role == UserRole.PROGRAMMER:
        return query.filter(Codebase.owner_id == user.user_id)
    if user.role == UserRole.TEAM_LEAD:
        owned_teams = db.query(Team.team_id).filter(Team.team_lead_id == user.user_id)
        legacy_owners = db.query(User.user_id).filter(User.team_id.in_(owned_teams))
        return query.filter(or_(Codebase.team_id.in_(owned_teams),
                                 and_(Codebase.team_id.is_(None), Codebase.owner_id.in_(legacy_owners))))
    return query.join(Project).filter(Project.project_lead_id == user.user_id)


def codebases_in_team(db, query, team_id):
    legacy_owners = db.query(User.user_id).filter(User.team_id == team_id)
    return query.filter(or_(Codebase.team_id == team_id,
                            and_(Codebase.team_id.is_(None), Codebase.owner_id.in_(legacy_owners))))


def require_project_access(db, user, project_id):
    if not db.query(ProjectAccessRequest).filter_by(project_id=project_id, team_lead_id=user.user_id,
                                                  status=AccessStatus.APPROVED).first():
        raise HTTPException(403, "Project Lead approval is required before creating a team in this project")


def require_assignment(db, project_id, team_id, user=None):
    if db.get(Project, project_id) is None:
        raise HTTPException(404, "Project not found")
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")
    if team.project_id != project_id:
        raise HTTPException(422, "The selected team does not belong to this project")
    if user is not None and not db.query(TeamMembership).filter_by(team_id=team_id, programmer_id=user.user_id,
                                                                  status=MembershipStatus.APPROVED).first():
        raise HTTPException(403, "Team Lead approval is required before uploading to this team")
    return team

def scans_for(db, user):
    return db.query(Scan).filter(Scan.codebase_id.in_(
        codebases_for(db, user).with_entities(Codebase.codebase_id)))

def require_scan(db, user, scan_id):
    scan = scans_for(db, user).filter(Scan.scan_id == scan_id).first()
    if scan is None:
        raise HTTPException(404, "Scan not found or not accessible")
    return scan

def require_function(db, user, function_id, write=False):
    from app.models import Function
    func = db.get(Function, function_id)
    if func is None:
        raise HTTPException(404, "Function not found")
    scan = require_scan(db, user, func.source_file.scan_id)
    if write and (user.role != UserRole.PROGRAMMER or scan.initiated_by != user.user_id):
        raise HTTPException(403, "Only the owner may request or review AI assistance")
    return func

