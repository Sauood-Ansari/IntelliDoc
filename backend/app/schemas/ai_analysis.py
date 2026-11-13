from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.ai_analysis import AIAnalysisType, AIAnalysisStatus


class AIDraftRequest(BaseModel):
    include_type_hints: bool = True


class AIConsistencyRequest(BaseModel):
    depth: str = "standard"


class AIAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    analysis_id: UUID
    function_id: UUID
    provider: str
    analysis_type: AIAnalysisType
    result: Optional[str] = None
    timestamp: datetime
    status: AIAnalysisStatus
    review_status: str = "Pending"
    reviewed_text: Optional[str] = None
