import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Uuid, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class AIAnalysisType(str, Enum):
    DRAFT_GENERATION = "Draft Generation"
    CONSISTENCY_CHECK = "Consistency Check"


class AIAnalysisStatus(str, Enum):
    REQUESTED = "Requested"
    COMPLETED = "Completed"
    FAILED = "Failed"


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    analysis_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    function_id = Column(Uuid, ForeignKey("functions.function_id"), nullable=False)
    provider = Column(String(50), default="Groq", nullable=False)  # SRS: Groq (Llama 3.3 70B)
    analysis_type = Column(SAEnum(AIAnalysisType, native_enum=False), nullable=False)
    result = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SAEnum(AIAnalysisStatus, native_enum=False), default=AIAnalysisStatus.REQUESTED, nullable=False)

    review_status = Column(String(20), nullable=False, default="Pending")
    reviewed_text = Column(Text, nullable=True)

    # Relationships
    function = relationship("Function", back_populates="ai_analyses")

