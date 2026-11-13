import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class ScanStatus(str, Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    PARTIAL = "Partial"
    FAILED = "Failed"


class ParseStatus(str, Enum):
    PARSED = "Parsed"
    FAILED = "Failed"


class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    codebase_id = Column(Uuid, ForeignKey("codebases.codebase_id"), nullable=False)
    initiated_by = Column(Uuid, ForeignKey("users.user_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SAEnum(ScanStatus, native_enum=False), default=ScanStatus.QUEUED, nullable=False)
    summary = Column(JSON, nullable=True)

    # Relationships
    codebase = relationship("Codebase", back_populates="scans")
    initiator = relationship("User", back_populates="scans")
    source_files = relationship("SourceFile", back_populates="scan", cascade="all, delete-orphan")
    score = relationship("Score", back_populates="scan", uselist=False, cascade="all, delete-orphan")


class SourceFile(Base):
    __tablename__ = "source_files"

    file_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    scan_id = Column(Uuid, ForeignKey("scans.scan_id"), nullable=False)
    path = Column(Text, nullable=False)
    parse_status = Column(SAEnum(ParseStatus, native_enum=False), default=ParseStatus.PARSED, nullable=False)

    error_message = Column(Text, nullable=True)

    # Relationships
    scan = relationship("Scan", back_populates="source_files")
    functions = relationship("Function", back_populates="source_file", cascade="all, delete-orphan")

