"""Delegated project access and many-to-many team memberships.

Preserve previously established assignments as explicitly labelled migration grants.
All new links go through the scoped lead approval APIs.
"""
import uuid
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from app.models import ProjectAccessRequest, TeamMembership, AccessStatus, MembershipStatus, Team, Project, User, Codebase, UserRole

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    ProjectAccessRequest.__table__.create(bind, checkfirst=True)
    TeamMembership.__table__.create(bind, checkfirst=True)
    access = ProjectAccessRequest.__table__
    memberships = TeamMembership.__table__
    note = "Preserved existing assignment during revision 0003 upgrade."
    now = datetime.utcnow()
    teams = bind.execute(sa.select(Team.team_id, Team.team_lead_id, Team.project_id, Project.project_lead_id)
        .join(Project, Project.project_id == Team.project_id)
        .join(User, User.user_id == Team.team_lead_id).where(User.role == UserRole.TEAM_LEAD)).all()
    for team_id, lead_id, project_id, project_lead_id in teams:
        found = bind.execute(sa.select(access.c.request_id).where(access.c.project_id == project_id,
            access.c.team_lead_id == lead_id)).first()
        if found is None:
            bind.execute(access.insert().values(request_id=uuid.uuid4(), project_id=project_id, team_lead_id=lead_id,
                status=AccessStatus.APPROVED, requested_at=now, decided_at=now, decided_by=project_lead_id, decision_note=note))
        owners = sa.select(Codebase.owner_id).where(Codebase.team_id == team_id, Codebase.project_id == project_id)
        users = bind.execute(sa.select(User.user_id).where(User.role == UserRole.PROGRAMMER,
            sa.or_(User.team_id == team_id, User.user_id.in_(owners)))).scalars().all()
        for programmer_id in users:
            found = bind.execute(sa.select(memberships.c.membership_id).where(memberships.c.team_id == team_id,
                memberships.c.programmer_id == programmer_id)).first()
            if found is None:
                bind.execute(memberships.insert().values(membership_id=uuid.uuid4(), team_id=team_id,
                    programmer_id=programmer_id, status=MembershipStatus.APPROVED, requested_at=now,
                    decided_at=now, decided_by=lead_id, decision_note=note))


def downgrade():
    raise RuntimeError("Restore a pre-migration backup to undo approval records safely")
