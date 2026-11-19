from fastapi import APIRouter, Depends, Query
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Codebase, Project
from app.schemas.codebase import CodebaseCreate, CodebaseOut
from app.dependencies import get_current_user, allow_programmer
from app.access import codebases_for, codebases_in_team, require_assignment

router = APIRouter(prefix="/codebases", tags=["Codebases"])

@router.post("", response_model=CodebaseOut, status_code=201)
def create(data: CodebaseCreate, user=Depends(allow_programmer), db: Session = Depends(get_db)):
    require_assignment(db, data.project_id, data.team_id, user)
    record = Codebase(name=data.name, owner_id=user.user_id, project_id=data.project_id, team_id=data.team_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("", response_model=list[CodebaseOut])
def list_codebases(user=Depends(get_current_user), db: Session = Depends(get_db),
                   project_id: UUID | None = None, team_id: UUID | None = None,
                   offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    query = codebases_for(db, user)
    if project_id is not None:
        query = query.filter(Codebase.project_id == project_id)
    if team_id is not None:
        query = codebases_in_team(db, query, team_id)
    return query.order_by(Codebase.name, Codebase.codebase_id).offset(offset).limit(limit).all()

