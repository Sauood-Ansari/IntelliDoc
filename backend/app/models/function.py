import uuid
from enum import Enum
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Uuid, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class SeverityLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Function(Base):
    __tablename__ = "functions"

    function_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    file_id = Column(Uuid, ForeignKey("source_files.file_id"), nullable=False)
    name = Column(String(255), nullable=False)
    line_number = Column(Integer, nullable=False)
    signature = Column(Text, nullable=False)
    docstring = Column(Text, nullable=True)  # NULL indicates missing documentation (SRS §2.1)

    source_code = Column(Text, nullable=False, default="")
    qualified_name = Column(String(1000), nullable=False, default="")

    @property
    def has_docstring(self):
        return bool(self.docstring and self.docstring.strip())

    @property
    def file_path(self):
        return self.source_file.path

    # Relationships
    source_file = relationship("SourceFile", back_populates="functions")
    findings = relationship("DocumentationFinding", back_populates="function", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="function", cascade="all, delete-orphan")


class DocumentationFinding(Base):
    __tablename__ = "documentation_findings"

    finding_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    function_id = Column(Uuid, ForeignKey("functions.function_id"), nullable=False)
    type = Column(String(100), nullable=False)  # e.g., 'Missing Documentation', 'Missing Parameter', 'Obsolete Parameter'
    severity = Column(SAEnum(SeverityLevel, native_enum=False), default=SeverityLevel.MEDIUM, nullable=False)
    explanation = Column(Text, nullable=False)

    # Relationships
    function = relationship("Function", back_populates="findings")

