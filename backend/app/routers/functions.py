from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, allow_programmer
from app.access import require_function
from app.models import AIAnalysis, AIAnalysisType, AIAnalysisStatus
from app.schemas.function import FunctionDetailOut
from app.schemas.ai_analysis import AIAnalysisOut
from app.services.ai_service import AIService

router = APIRouter(prefix="/functions", tags=["Functions and AI"])

@router.get("/{function_id}", response_model=FunctionDetailOut)
def detail(function_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return require_function(db, user, function_id)

@router.get("/{function_id}/analyses", response_model=list[AIAnalysisOut])
def analyses(function_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return require_function(db, user, function_id).ai_analyses

async def run_ai(function_id, kind, user, db):
    func = require_function(db, user, function_id, write=True)
    if kind == "draft" and func.docstring and func.docstring.strip():
        raise HTTPException(409, "Draft generation is for undocumented functions")
    if kind == "check" and not (func.docstring and func.docstring.strip()):
        raise HTTPException(409, "A consistency check requires an existing docstring")
    result = await AIService.request(kind, func.source_code)
    record = AIAnalysis(function_id=function_id, provider=result["provider"],
                        analysis_type=AIAnalysisType.DRAFT_GENERATION if kind == "draft" else AIAnalysisType.CONSISTENCY_CHECK,
                        status=AIAnalysisStatus(result["status"]), result=result["result"], review_status="Pending")
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.post("/{function_id}/generate-doc", response_model=AIAnalysisOut)
async def draft(function_id: UUID, user=Depends(allow_programmer), db: Session = Depends(get_db)):
    return await run_ai(function_id, "draft", user, db)

@router.post("/{function_id}/consistency-check", response_model=AIAnalysisOut)
async def check(function_id: UUID, user=Depends(allow_programmer), db: Session = Depends(get_db)):
    return await run_ai(function_id, "check", user, db)

class Review(BaseModel):
    decision: Literal["Accepted", "Rejected"]
    edited_text: str | None = Field(None, max_length=20000)

@router.patch("/{function_id}/analyses/{analysis_id}", response_model=AIAnalysisOut)
def review(function_id: UUID, analysis_id: UUID, body: Review,
           user=Depends(allow_programmer), db: Session = Depends(get_db)):
    require_function(db, user, function_id, write=True)
    record = db.get(AIAnalysis, analysis_id)
    if not record or record.function_id != function_id:
        raise HTTPException(404, "Analysis not found")
    if record.status != AIAnalysisStatus.COMPLETED or record.analysis_type != AIAnalysisType.DRAFT_GENERATION:
        raise HTTPException(409, "Only completed documentation drafts can be reviewed")
    if body.decision == "Accepted" and not (body.edited_text or record.result or "").strip():
        raise HTTPException(422, "Accepted documentation cannot be empty")
    record.review_status = body.decision
    record.reviewed_text = body.edited_text if body.edited_text is not None else record.result
    db.commit()
    db.refresh(record)
    return record

