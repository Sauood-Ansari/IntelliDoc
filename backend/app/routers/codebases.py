from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Codebase, Project
from app.schemas.codebase import CodebaseCreate, CodebaseOut
from app.dependencies import get_current_user, allow_programmer
from app.access import codebases_for

router = APIRouter(prefix="/codebases", tags=["Codebases"])

@router.post("", response_model=CodebaseOut, status_code=201)
def create(data: CodebaseCreate, user=Depends(allow_programmer), db: Session = Depends(get_db)):
    if data.project_id and not codebases_for(db, user).filter(Codebase.project_id == data.project_id).first():
        raise HTTPException(403, "A project lead must assign your first codebase to this project")
    record = Codebase(name=data.name, owner_id=user.user_id, project_id=data.project_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("", response_model=list[CodebaseOut])
def list_codebases(user=Depends(get_current_user), db: Session = Depends(get_db),
                   offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return codebases_for(db, user).order_by(Codebase.name).offset(offset).limit(limit).all()

