import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Enum as SAEnum
from sqlalchemy.orm import relationship, validates
from app.models.base import Base
from app.core.names import clean_name, name_key


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
    led_teams = relationship("Team", foreign_keys="Team.team_lead_id", back_populates="leader")
    led_projects = relationship("Project", back_populates="project_lead")
    codebases = relationship("Codebase", back_populates="owner")
    scans = relationship("Scan", back_populates="initiator")
    scores = relationship("Score", back_populates="programmer")


class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    team_name = Column(String(100), unique=True, nullable=False)
    name_key = Column(String(300), unique=True, nullable=False)
    team_lead_id = Column(Uuid, ForeignKey("users.user_id", use_alter=True, name="fk_teams_team_lead_id"), nullable=True)
    project_id = Column(Uuid, ForeignKey("projects.project_id", name="fk_teams_project_id"), nullable=True)

    # Relationships
    leader = relationship("User", foreign_keys=[team_lead_id], back_populates="led_teams")
    members = relationship("User", foreign_keys=[User.team_id], back_populates="team")
    project = relationship("Project", back_populates="teams")
    codebases = relationship("Codebase", back_populates="team")

    @validates("team_name")
    def validate_name(self, key, value):
        self.name_key = name_key(value)
        return clean_name(value)

    @property
    def project_name(self):
        return self.project.project_name if self.project else None


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    project_name = Column(String(150), nullable=False)
    name_key = Column(String(300), unique=True, nullable=False)
    project_lead_id = Column(Uuid, ForeignKey("users.user_id"), nullable=False)

    # Relationships
    project_lead = relationship("User", back_populates="led_projects")
    codebases = relationship("Codebase", back_populates="project")
    teams = relationship("Team", back_populates="project")

    @validates("project_name")
    def validate_name(self, key, value):
        self.name_key = name_key(value)
        return clean_name(value)

