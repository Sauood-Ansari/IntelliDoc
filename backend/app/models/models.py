"""IntelliDoc — SQLAlchemy database models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


def now_utc():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    programmer = "programmer"
    team_lead = "team_lead"
    project_lead = "project_lead"


class ScanStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    partial = "partial"
    failed = "failed"


class FindingType(str, enum.Enum):
    no_docstring = "NO_DOCSTRING"
    missing_param_doc = "MISSING_PARAM_DOC"
    obsolete_param_doc = "OBSOLETE_PARAM_DOC"
    missing_return_doc = "MISSING_RETURN_DOC"


class FindingSeverity(str, enum.Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class AIAnalysisType(str, enum.Enum):
    doc_generation = "doc_generation"
    consistency_check = "consistency_check"


class AIAnalysisStatus(str, enum.Enum):
    requested = "requested"
    completed = "completed"
    failed = "failed"


# ─── Models ───────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    project_lead_id = Column(String, ForeignKey("users.id"), nullable=True)
    project_lead = relationship("User", foreign_keys=[project_lead_id], back_populates="led_projects")
    teams = relationship("Team", back_populates="project")


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project", back_populates="teams")

    team_lead_id = Column(String, ForeignKey("users.id"), nullable=True)
    team_lead = relationship("User", foreign_keys=[team_lead_id], back_populates="led_teams")

    members = relationship("User", foreign_keys="User.team_id", back_populates="team")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.programmer)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    is_active = Column(Boolean, default=True)

    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    team = relationship("Team", foreign_keys=[team_id], back_populates="members")

    led_teams = relationship("Team", foreign_keys="Team.team_lead_id", back_populates="team_lead")
    led_projects = relationship("Project", foreign_keys="Project.project_lead_id", back_populates="project_lead")

    scans = relationship("Scan", back_populates="initiator")
    scores = relationship("Score", back_populates="programmer")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(300), nullable=False)
    status = Column(SAEnum(ScanStatus), default=ScanStatus.queued)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    total_files = Column(Integer, default=0)
    parsed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    total_functions = Column(Integer, default=0)
    documented_functions = Column(Integer, default=0)

    initiated_by = Column(String, ForeignKey("users.id"), nullable=False)
    initiator = relationship("User", back_populates="scans")

    source_files = relationship("SourceFile", back_populates="scan", cascade="all, delete-orphan")
    score = relationship("Score", back_populates="scan", uselist=False)


class SourceFile(Base):
    __tablename__ = "source_files"

    id = Column(String, primary_key=True, default=gen_uuid)
    path = Column(String(500), nullable=False)
    parse_status = Column(String(50), default="ok")
    parse_error = Column(Text, nullable=True)
    function_count = Column(Integer, default=0)

    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    scan = relationship("Scan", back_populates="source_files")

    functions = relationship("Function", back_populates="source_file", cascade="all, delete-orphan")


class Function(Base):
    __tablename__ = "functions"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    line_number = Column(Integer, nullable=False)
    signature = Column(Text)
    docstring = Column(Text, nullable=True)
    has_docstring = Column(Boolean, default=False)
    source_body = Column(Text, nullable=True)
    params = Column(JSON, default=list)  # list of param names
    has_return_statement = Column(Boolean, default=False)

    file_id = Column(String, ForeignKey("source_files.id"), nullable=False)
    source_file = relationship("SourceFile", back_populates="functions")

    findings = relationship("DocumentationFinding", back_populates="function", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="function", cascade="all, delete-orphan")


class DocumentationFinding(Base):
    __tablename__ = "documentation_findings"

    id = Column(String, primary_key=True, default=gen_uuid)
    finding_type = Column(SAEnum(FindingType), nullable=False)
    severity = Column(SAEnum(FindingSeverity), nullable=False)
    explanation = Column(Text, nullable=False)
    extra = Column(JSON, default=dict)  # e.g. {"param": "tax"}

    function_id = Column(String, ForeignKey("functions.id"), nullable=False)
    function = relationship("Function", back_populates="findings")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(String, primary_key=True, default=gen_uuid)
    analysis_type = Column(SAEnum(AIAnalysisType), nullable=False)
    provider = Column(String(100), nullable=False)
    status = Column(SAEnum(AIAnalysisStatus), default=AIAnalysisStatus.requested)
    result = Column(Text, nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    function_id = Column(String, ForeignKey("functions.id"), nullable=False)
    function = relationship("Function", back_populates="ai_analyses")


class Score(Base):
    __tablename__ = "scores"

    id = Column(String, primary_key=True, default=gen_uuid)
    total_score = Column(Float, nullable=False, default=0.0)
    completeness_score = Column(Float, default=0.0)
    param_consistency_score = Column(Float, default=0.0)
    return_consistency_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, unique=True)
    scan = relationship("Scan", back_populates="score")

    programmer_id = Column(String, ForeignKey("users.id"), nullable=False)
    programmer = relationship("User", back_populates="scores")
