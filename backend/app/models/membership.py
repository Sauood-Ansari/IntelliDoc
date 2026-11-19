"""Project access and per-team membership approvals, independent of signup role."""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class AccessStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class MembershipStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class ProjectAccessRequest(Base):
    __tablename__ = "project_access_requests"
    __table_args__ = (UniqueConstraint("project_id", "team_lead_id", name="uq_project_access_lead"),)
    request_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid, ForeignKey("projects.project_id"), nullable=False, index=True)
    team_lead_id = Column(Uuid, ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(SAEnum(AccessStatus), nullable=False, default=AccessStatus.PENDING)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(Uuid, ForeignKey("users.user_id"), nullable=True)
    decision_note = Column(String(500), nullable=True)
    project = relationship("Project")
    requester = relationship("User", foreign_keys=[team_lead_id])

    @property
    def project_name(self): return self.project.project_name
    @property
    def requester_name(self): return self.requester.name
    @property
    def requester_email(self): return self.requester.email


class TeamMembership(Base):
    __tablename__ = "team_memberships"
    __table_args__ = (UniqueConstraint("team_id", "programmer_id", name="uq_team_membership_programmer"),)
    membership_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id = Column(Uuid, ForeignKey("teams.team_id"), nullable=False, index=True)
    programmer_id = Column(Uuid, ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(SAEnum(MembershipStatus), nullable=False, default=MembershipStatus.PENDING)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(Uuid, ForeignKey("users.user_id"), nullable=True)
    decision_note = Column(String(500), nullable=True)
    team = relationship("Team")
    requester = relationship("User", foreign_keys=[programmer_id])

    @property
    def project_id(self): return self.team.project_id
    @property
    def project_name(self): return self.team.project_name
    @property
    def team_name(self): return self.team.team_name
    @property
    def requester_name(self): return self.requester.name
    @property
    def requester_email(self): return self.requester.email
