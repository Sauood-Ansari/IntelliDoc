"""Shared scope for every resource endpoint."""
from fastapi import HTTPException
from app.models import Codebase, Scan, User, Team, Project, UserRole

def codebases_for(db, user):
    query = db.query(Codebase)
    if user.role == UserRole.PROGRAMMER:
        return query.filter(Codebase.owner_id == user.user_id)
    if user.role == UserRole.TEAM_LEAD:
        return query.join(User, Codebase.owner_id == User.user_id).join(
            Team, User.team_id == Team.team_id).filter(Team.team_lead_id == user.user_id)
    return query.join(Project).filter(Project.project_lead_id == user.user_id)

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

