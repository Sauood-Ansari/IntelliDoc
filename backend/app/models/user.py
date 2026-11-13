import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserRole(str, Enum):
    PROGRAMMER = "Programmer"
    TEAM_LEAD = "Team Lead"
    PROJECT_LEAD = "Project Lead"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole, native_enum=False), nullable=False)
    team_id = Column(Uuid, ForeignKey("teams.team_id", use_alter=True, name="fk_users_team_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    team = relationship("Team", foreign_keys=[team_id], back_populates="members")
    led_team = relationship("Team", foreign_keys="Team.team_lead_id", back_populates="leader", uselist=False)
    led_projects = relationship("Project", back_populates="project_lead")
    codebases = relationship("Codebase", back_populates="owner")
    scans = relationship("Scan", back_populates="initiator")
    scores = relationship("Score", back_populates="programmer")


class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    team_name = Column(String(100), unique=True, nullable=False)
    team_lead_id = Column(Uuid, ForeignKey("users.user_id", use_alter=True, name="fk_teams_team_lead_id"), unique=True, nullable=True)

    # Relationships
    leader = relationship("User", foreign_keys=[team_lead_id], back_populates="led_team")
    members = relationship("User", foreign_keys=[User.team_id], back_populates="team")


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    project_name = Column(String(150), nullable=False)
    project_lead_id = Column(Uuid, ForeignKey("users.user_id"), nullable=False)

    # Relationships
    project_lead = relationship("User", back_populates="led_projects")
    codebases = relationship("Codebase", back_populates="project")

