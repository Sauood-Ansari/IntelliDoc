"""IntelliDoc — Scans router with background worker pattern."""
import json
import os
import tempfile
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.models import (
    User, UserRole, Scan, ScanStatus, SourceFile, Function,
    DocumentationFinding, FindingType, FindingSeverity, Score, AIAnalysis,
    AIAnalysisType, AIAnalysisStatus,
)
from app.schemas.schemas import ScanOut, ScanListItem, FindingOut, FindingPage, FunctionOut
from app.analysis.engine import analyse_codebase, safe_extract_archive, SecurityError
from app.analysis.ai_service import generate_docstring, check_consistency, AIServiceError
from app.core.rate_limit import limiter

router = APIRouter(prefix="/scans", tags=["Scans"])


# ─── Background Worker ────────────────────────────────────────────────────────

def _run_scan_worker(scan_id: str, archive_path: str, db_url: str):
    """Synchronous scan worker — runs in a background thread."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    DbSession = sessionmaker(bind=engine)
    db = DbSession()

    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        scan.status = ScanStatus.running
        db.commit()

        # Extract archive to temp dir
        with tempfile.TemporaryDirectory(prefix="intellidoc_") as tmpdir:
            try:
                safe_extract_archive(archive_path, tmpdir)
            except SecurityError as e:
                scan.status = ScanStatus.failed
                scan.error_message = str(e)
                db.commit()
                return
            except Exception as e:
                scan.status = ScanStatus.failed
                scan.error_message = f"Archive extraction failed: {str(e)}"
                db.commit()
                return

            # Run analysis
            result = analyse_codebase(tmpdir)

        # Persist file and function data
        scan.total_files = result.total_files
        scan.parsed_files = result.parsed_files
        scan.failed_files = result.failed_files
        scan.total_functions = result.total_functions
        scan.documented_functions = result.documented_functions

        for file_result in result.files:
            sf = SourceFile(
                path=file_result.path,
                parse_status=file_result.parse_status,
                parse_error=file_result.parse_error,
                function_count=len(file_result.functions),
                scan_id=scan_id,
            )
            db.add(sf)
            db.flush()

            for func_meta in file_result.functions:
                func = Function(
                    name=func_meta.name,
                    line_number=func_meta.line_number,
                    signature=f"{func_meta.name}({', '.join(func_meta.params)})",
                    docstring=func_meta.docstring_data.raw if func_meta.docstring_data else None,
                    has_docstring=func_meta.has_docstring,
                    source_body=func_meta.source_body,
                    params=func_meta.params,
                    has_return_statement=func_meta.has_return_statement,
                    file_id=sf.id,
                )
                db.add(func)
                db.flush()

                findings_list = file_result.findings_by_function.get(func_meta.name, [])
                for finding in findings_list:
                    df = DocumentationFinding(
                        finding_type=FindingType(finding.finding_type),
                        severity=FindingSeverity(finding.severity),
                        explanation=finding.explanation,
                        extra=finding.extra,
                        function_id=func.id,
                    )
                    db.add(df)

        # Compute and persist score
        score = Score(
            total_score=result.score,
            completeness_score=result.completeness_score,
            param_consistency_score=result.param_consistency_score,
            return_consistency_score=result.return_consistency_score,
            scan_id=scan_id,
            programmer_id=scan.initiated_by,
        )
        db.add(score)

        has_failures = result.failed_files > 0
        scan.status = ScanStatus.partial if has_failures else ScanStatus.completed
        scan.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        db.rollback()
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = ScanStatus.failed
                scan.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        # Clean up archive
        try:
            os.unlink(archive_path)
        except Exception:
            pass


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", status_code=202)
async def create_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.programmer)),
    db: Session = Depends(get_db),
):
    """Submit a Python codebase ZIP for analysis (async background processing)."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archives are supported")

    # Save archive to temp file
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", prefix="intellidoc_upload_")
    try:
        content = await file.read()
        max_bytes = 10 * 1024 * 1024  # 10 MB compressed limit
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="Archive exceeds 10 MB compressed size limit")
        tmp_file.write(content)
        tmp_file.close()
    except HTTPException:
        tmp_file.close()
        os.unlink(tmp_file.name)
        raise

    # Create scan record
    from app.core.config import settings
    scan = Scan(
        name=file.filename.removesuffix(".zip"),
        status=ScanStatus.queued,
        initiated_by=current_user.id,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Launch background worker
    background_tasks.add_task(
        _run_scan_worker, scan.id, tmp_file.name, settings.DATABASE_URL
    )

    return {"scan_id": scan.id, "status": "queued", "message": "Scan queued for processing"}


@router.get("", response_model=list[ScanListItem])
def list_scans(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List scans for the current user (programmers) or authorized users (leads)."""
    offset = (page - 1) * per_page
    query = db.query(Scan).filter(Scan.initiated_by == current_user.id)

    if current_user.role in (UserRole.team_lead, UserRole.project_lead):
        # Also include team members' scans
        if current_user.role == UserRole.team_lead and current_user.led_teams:
            team_ids = [t.id for t in current_user.led_teams]
            from sqlalchemy import or_
            team_member_ids = [
                u.id for u in db.query(User).filter(User.team_id.in_(team_ids)).all()
            ]
            query = db.query(Scan).filter(
                or_(Scan.initiated_by == current_user.id,
                    Scan.initiated_by.in_(team_member_ids))
            )

    scans = query.order_by(Scan.created_at.desc()).offset(offset).limit(per_page).all()

    result = []
    for scan in scans:
        score_val = scan.score.total_score if scan.score else None
        result.append(ScanListItem(
            id=scan.id,
            name=scan.name,
            status=scan.status.value,
            created_at=scan.created_at,
            total_functions=scan.total_functions,
            documented_functions=scan.documented_functions,
            score_value=score_val,
        ))
    return result


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get scan status and summary (IDOR-protected)."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # IDOR check
    _check_scan_access(scan, current_user, db)

    return ScanOut.model_validate(scan)


@router.get("/{scan_id}/findings", response_model=FindingPage)
def get_scan_findings(
    scan_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    severity: str = Query(None),
    finding_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated findings for a scan."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    _check_scan_access(scan, current_user, db)

    query = (
        db.query(DocumentationFinding)
        .join(Function, DocumentationFinding.function_id == Function.id)
        .join(SourceFile, Function.file_id == SourceFile.id)
        .filter(SourceFile.scan_id == scan_id)
    )

    if severity:
        query = query.filter(DocumentationFinding.severity == severity)
    if finding_type:
        query = query.filter(DocumentationFinding.finding_type == finding_type)

    total = query.count()
    offset = (page - 1) * per_page
    findings = query.offset(offset).limit(per_page).all()

    items = []
    for f in findings:
        func = db.query(Function).filter(Function.id == f.function_id).first()
        sf = db.query(SourceFile).filter(SourceFile.id == func.file_id).first() if func else None
        items.append(FindingOut(
            id=f.id,
            finding_type=f.finding_type.value,
            severity=f.severity.value,
            explanation=f.explanation,
            extra=f.extra or {},
            function_id=f.function_id,
            function_name=func.name if func else None,
            function_line=func.line_number if func else None,
            file_path=sf.path if sf else None,
        ))

    return FindingPage(total=total, page=page, per_page=per_page, items=items)


@router.get("/{scan_id}/functions", response_model=list[FunctionOut])
def get_scan_functions(
    scan_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get functions analysed in a scan."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    _check_scan_access(scan, current_user, db)

    source_file_ids = [sf.id for sf in db.query(SourceFile).filter(SourceFile.scan_id == scan_id).all()]
    offset = (page - 1) * per_page
    funcs = (
        db.query(Function)
        .filter(Function.file_id.in_(source_file_ids))
        .offset(offset)
        .limit(per_page)
        .all()
    )

    result = []
    for func in funcs:
        sf = db.query(SourceFile).filter(SourceFile.id == func.file_id).first()
        findings = [
            FindingOut(
                id=f.id,
                finding_type=f.finding_type.value,
                severity=f.severity.value,
                explanation=f.explanation,
                extra=f.extra or {},
                function_id=f.function_id,
                function_name=func.name,
                function_line=func.line_number,
                file_path=sf.path if sf else None,
            )
            for f in func.findings
        ]
        from app.schemas.schemas import AIAnalysisOut
        ai_analyses = [AIAnalysisOut.model_validate(a) for a in func.ai_analyses]
        result.append(FunctionOut(
            id=func.id,
            name=func.name,
            line_number=func.line_number,
            signature=func.signature,
            has_docstring=func.has_docstring,
            docstring=func.docstring,
            params=func.params or [],
            has_return_statement=func.has_return_statement,
            file_path=sf.path if sf else None,
            findings=findings,
            ai_analyses=ai_analyses,
        ))
    return result


# ─── AI Endpoints ─────────────────────────────────────────────────────────────

@router.post("/functions/{function_id}/generate-doc")
@limiter.limit("5/minute")
async def generate_doc(
    request: Request,
    function_id: str,
    current_user: User = Depends(require_role(UserRole.programmer)),
    db: Session = Depends(get_db),
):
    """Request AI-generated draft docstring for an undocumented function."""
    func = db.query(Function).filter(Function.id == function_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")

    _check_function_access(func, current_user, db)

    analysis = AIAnalysis(
        analysis_type=AIAnalysisType.doc_generation,
        provider="groq",
        status=AIAnalysisStatus.requested,
        function_id=function_id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    try:
        result = await generate_docstring(func.name, func.params or [], func.source_body or "")
        analysis.status = AIAnalysisStatus.completed
        analysis.result = result["docstring"]
        analysis.provider = result["provider"]
        db.commit()
        return {
            "analysis_id": analysis.id,
            "docstring": result["docstring"],
            "is_mock": result["is_mock"],
            "provider": result["provider"],
        }
    except AIServiceError as e:
        analysis.status = AIAnalysisStatus.failed
        analysis.error_detail = str(e)
        db.commit()
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")


@router.post("/functions/{function_id}/consistency-check")
@limiter.limit("5/minute")
async def consistency_check(
    request: Request,
    function_id: str,
    current_user: User = Depends(require_role(UserRole.programmer)),
    db: Session = Depends(get_db),
):
    """Request AI logical-consistency check for a documented function."""
    func = db.query(Function).filter(Function.id == function_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")

    _check_function_access(func, current_user, db)

    if not func.has_docstring:
        raise HTTPException(status_code=400, detail="Function has no docstring to check")

    analysis = AIAnalysis(
        analysis_type=AIAnalysisType.consistency_check,
        provider="gemini",
        status=AIAnalysisStatus.requested,
        function_id=function_id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    try:
        result = await check_consistency(
            func.name, func.params or [], func.source_body or "", func.docstring or ""
        )
        analysis.status = AIAnalysisStatus.completed
        analysis.result = json.dumps(result)
        analysis.provider = result["provider"]
        db.commit()
        return {**result, "analysis_id": analysis.id}
    except AIServiceError as e:
        analysis.status = AIAnalysisStatus.failed
        analysis.error_detail = str(e)
        db.commit()
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")


# ─── Standalone Function Detail ────────────────────────────────────────────────

@router.get("/functions/{function_id}", response_model=FunctionOut)
def get_function_detail(
    function_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed information about a single function (SRS Appendix B)."""
    func = db.query(Function).filter(Function.id == function_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")

    _check_function_access(func, current_user, db)

    sf = db.query(SourceFile).filter(SourceFile.id == func.file_id).first()
    findings = [
        FindingOut(
            id=f.id,
            finding_type=f.finding_type.value,
            severity=f.severity.value,
            explanation=f.explanation,
            extra=f.extra or {},
            function_id=f.function_id,
            function_name=func.name,
            function_line=func.line_number,
            file_path=sf.path if sf else None,
        )
        for f in func.findings
    ]
    from app.schemas.schemas import AIAnalysisOut
    ai_analyses = [AIAnalysisOut.model_validate(a) for a in func.ai_analyses]

    return FunctionOut(
        id=func.id,
        name=func.name,
        line_number=func.line_number,
        signature=func.signature,
        has_docstring=func.has_docstring,
        docstring=func.docstring,
        params=func.params or [],
        has_return_statement=func.has_return_statement,
        file_path=sf.path if sf else None,
        findings=findings,
        ai_analyses=ai_analyses,
    )


# ─── Access Control Helpers ────────────────────────────────────────────────────

def _check_scan_access(scan: Scan, user: User, db: Session):
    """Raise 403 if user is not authorized to access this scan."""
    if scan.initiated_by == user.id:
        return
    if user.role == UserRole.team_lead:
        team_member_ids = [u.id for u in db.query(User).filter(
            User.team_id.in_([t.id for t in user.led_teams])
        ).all()]
        if scan.initiated_by in team_member_ids:
            return
    if user.role == UserRole.project_lead:
        return  # Project leads can see all (simplification; refine with project membership)
    raise HTTPException(status_code=403, detail="Access denied")


def _check_function_access(func: Function, user: User, db: Session):
    """Check that the user owns the scan containing this function."""
    sf = db.query(SourceFile).filter(SourceFile.id == func.file_id).first()
    if not sf:
        raise HTTPException(status_code=404, detail="Source file not found")
    scan = db.query(Scan).filter(Scan.id == sf.scan_id).first()
    if not scan or scan.initiated_by != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
