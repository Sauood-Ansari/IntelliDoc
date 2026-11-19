from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Scan, ScanStatus, Codebase
from app.schemas.scan import ScanOut, SourceFileOut
from app.schemas.function import FunctionDetailOut, FindingOut
from app.dependencies import get_current_user, allow_programmer
from app.services.scan_service import ScanService
from app.config import settings
from app.access import scans_for, require_scan, require_assignment, codebases_for, codebases_in_team

router = APIRouter(prefix="/scans", tags=["Scans"])

@router.post("", response_model=ScanOut, status_code=201)
async def start_scan(codebase_id: UUID = Form(...), file: UploadFile = File(...),
                     project_id: UUID = Form(...), team_id: UUID = Form(...),
                     user=Depends(allow_programmer), db: Session = Depends(get_db)):
    codebase = db.get(Codebase, codebase_id)
    if not codebase or codebase.owner_id != user.user_id:
        raise HTTPException(404, "Codebase not found")
    require_assignment(db, project_id, team_id, user)
    if ((codebase.project_id is not None and codebase.project_id != project_id)
            or (codebase.team_id is not None and codebase.team_id != team_id)):
        raise HTTPException(409, "This codebase belongs to another project or team. Create a new codebase for that assignment.")
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Upload a ZIP archive containing Python files")
    content = await file.read(settings.MAX_SOURCE_SIZE + 1)
    await file.close()
    if len(content) > settings.MAX_SOURCE_SIZE:
        raise HTTPException(413, "ZIP upload exceeds 10 MB")
    # Legacy codebases receive their first explicit assignment on upload.
    codebase.project_id, codebase.team_id = project_id, team_id
    scan = Scan(codebase_id=codebase_id, initiated_by=user.user_id, status=ScanStatus.RUNNING)
    db.add(scan)
    db.commit()
    scan_id = scan.scan_id
    try:
        return await run_in_threadpool(ScanService.execute_scan_on_zip, db, scan_id, content)
    except ValueError as exc:
        db.rollback()
        scan = db.get(Scan, scan_id)
        scan.status, scan.summary = ScanStatus.FAILED, {"error": str(exc)}
        db.commit()
        raise HTTPException(400, str(exc))
    except Exception:
        db.rollback()
        scan = db.get(Scan, scan_id)
        scan.status, scan.summary = ScanStatus.FAILED, {"error": "Scan failed; please retry with a smaller archive"}
        db.commit()
        raise HTTPException(500, "Unable to process scan")

@router.get("", response_model=list[ScanOut])
def list_scans(user=Depends(get_current_user), db: Session = Depends(get_db),
               project_id: UUID | None = None, team_id: UUID | None = None,
               offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    query = scans_for(db, user)
    codebases = codebases_for(db, user)
    if project_id is not None:
        codebases = codebases.filter(Codebase.project_id == project_id)
    if team_id is not None:
        codebases = codebases_in_team(db, codebases, team_id)
    return query.filter(Scan.codebase_id.in_(codebases.with_entities(Codebase.codebase_id))).order_by(
        Scan.timestamp.desc(), Scan.scan_id.desc()).offset(offset).limit(limit).all()

@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return require_scan(db, user, scan_id)

@router.get("/{scan_id}/files", response_model=list[SourceFileOut])
def files(scan_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return require_scan(db, user, scan_id).source_files

@router.get("/{scan_id}/functions", response_model=list[FunctionDetailOut])
def functions(scan_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return [f for sf in require_scan(db, user, scan_id).source_files for f in sf.functions]

@router.get("/{scan_id}/findings", response_model=list[FindingOut])
def findings(scan_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return [finding for sf in require_scan(db, user, scan_id).source_files for f in sf.functions for finding in f.findings]

