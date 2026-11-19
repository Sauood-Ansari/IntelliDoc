"""Delegated approvals: Project Lead approves Team Lead; Team Lead approves Programmer."""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_user, allow_programmer, allow_team_lead, allow_project_lead
from app.models import Project, Team, UserRole, ProjectAccessRequest, TeamMembership, AccessStatus, MembershipStatus
from app.schemas.membership import ProjectAccessCreate, TeamMembershipCreate, ApprovalDecision, ProjectAccessOut, TeamMembershipOut

router = APIRouter(tags=["Membership approvals"])


def commit_request(db, record, lookup):
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Concurrent duplicate submissions share the existing membership, not two records.
        record = lookup().first()
        if record is None:
            raise HTTPException(409, "Request changed. Refresh and retry.")
    db.refresh(record)
    return record


@router.post("/project-access-requests", response_model=ProjectAccessOut)
def request_project(body: ProjectAccessCreate, user=Depends(allow_team_lead), db: Session = Depends(get_db)):
    if db.get(Project, body.project_id) is None:
        raise HTTPException(404, "Project not found")
    def lookup():
        return db.query(ProjectAccessRequest).filter_by(project_id=body.project_id, team_lead_id=user.user_id)
    record = lookup().first()
    if record and record.status != AccessStatus.REJECTED:
        return record
    if record is None:
        record = ProjectAccessRequest(project_id=body.project_id, team_lead_id=user.user_id)
    else:
        record.status = AccessStatus.PENDING
        record.requested_at = datetime.utcnow()
        record.decided_at = record.decided_by = record.decision_note = None
    return commit_request(db, record, lookup)


@router.get("/project-access-requests", response_model=list[ProjectAccessOut])
def project_requests(user=Depends(get_current_user), db: Session = Depends(get_db),
                     project_id: UUID | None = None, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    query = db.query(ProjectAccessRequest).options(joinedload(ProjectAccessRequest.project), joinedload(ProjectAccessRequest.requester))
    if user.role == UserRole.TEAM_LEAD:
        query = query.filter(ProjectAccessRequest.team_lead_id == user.user_id)
    elif user.role == UserRole.PROJECT_LEAD:
        query = query.join(Project).filter(Project.project_lead_id == user.user_id)
    else:
        raise HTTPException(403, "Project access requests are for leads")
    if project_id is not None:
        query = query.filter(ProjectAccessRequest.project_id == project_id)
    return query.order_by(ProjectAccessRequest.requested_at.desc(), ProjectAccessRequest.request_id).offset(offset).limit(limit).all()


@router.patch("/project-access-requests/{request_id}", response_model=ProjectAccessOut)
def decide_project(request_id: UUID, body: ApprovalDecision, user=Depends(allow_project_lead), db: Session = Depends(get_db)):
    # Serialize competing decisions on PostgreSQL and use a conditional update on SQLite too.
    record = db.query(ProjectAccessRequest).join(Project).filter(ProjectAccessRequest.request_id == request_id,
        Project.project_lead_id == user.user_id).first()
    if record is None:
        raise HTTPException(404, "Request not found or not accessible")
    target = AccessStatus.APPROVED if body.decision == "Approve" else AccessStatus.REJECTED
    if record.status != AccessStatus.PENDING:
        if record.status == target:
            return record
        raise HTTPException(409, "Only pending requests can be decided")
    changed = db.query(ProjectAccessRequest).filter_by(request_id=request_id, status=AccessStatus.PENDING).update({
        "status": target, "decided_by": user.user_id, "decided_at": datetime.utcnow(), "decision_note": body.note}, synchronize_session=False)
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Another decision was saved. Refresh the request.")
    db.commit(); db.refresh(record)
    return record


@router.post("/team-memberships", response_model=TeamMembershipOut)
def request_team(body: TeamMembershipCreate, user=Depends(allow_programmer), db: Session = Depends(get_db)):
    team = db.get(Team, body.team_id)
    if team is None or team.project_id is None or team.team_lead_id is None:
        raise HTTPException(404, "Select a team with a project and Team Lead")
    def lookup():
        return db.query(TeamMembership).filter_by(team_id=body.team_id, programmer_id=user.user_id)
    record = lookup().first()
    if record and record.status != MembershipStatus.REJECTED:
        return record
    if record is None:
        record = TeamMembership(team_id=body.team_id, programmer_id=user.user_id)
    else:
        record.status = MembershipStatus.PENDING
        record.requested_at = datetime.utcnow()
        record.decided_at = record.decided_by = record.decision_note = None
    return commit_request(db, record, lookup)


@router.get("/team-memberships", response_model=list[TeamMembershipOut])
def team_memberships(user=Depends(get_current_user), db: Session = Depends(get_db),
                     team_id: UUID | None = None, project_id: UUID | None = None,
                     offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    query = db.query(TeamMembership).join(Team).options(joinedload(TeamMembership.team).joinedload(Team.project), joinedload(TeamMembership.requester))
    if user.role == UserRole.PROGRAMMER:
        query = query.filter(TeamMembership.programmer_id == user.user_id)
    elif user.role == UserRole.TEAM_LEAD:
        query = query.filter(Team.team_lead_id == user.user_id)
    else:
        query = query.join(Project).filter(Project.project_lead_id == user.user_id)
    if team_id is not None:
        query = query.filter(TeamMembership.team_id == team_id)
    if project_id is not None:
        query = query.filter(Team.project_id == project_id)
    return query.order_by(TeamMembership.requested_at.desc(), TeamMembership.membership_id).offset(offset).limit(limit).all()


@router.patch("/team-memberships/{membership_id}", response_model=TeamMembershipOut)
def decide_membership(membership_id: UUID, body: ApprovalDecision, user=Depends(allow_team_lead), db: Session = Depends(get_db)):
    query = db.query(TeamMembership).join(Team).filter(TeamMembership.membership_id == membership_id,
        Team.team_lead_id == user.user_id)
    expected = MembershipStatus.PENDING
    record = query.first()
    if record is None:
        raise HTTPException(404, "Membership not found or not accessible")
    if record.status != expected:
        raise HTTPException(409, "This request is not awaiting your approval. Refresh its status.")
    values = {"status": MembershipStatus.APPROVED if body.decision == "Approve" else MembershipStatus.REJECTED,
        "decided_by": user.user_id, "decided_at": datetime.utcnow(), "decision_note": body.note}
    changed = db.query(TeamMembership).filter_by(membership_id=membership_id, status=expected).update(values, synchronize_session=False)
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Another decision was saved. Refresh the request.")
    db.commit(); db.refresh(record)
    return record
