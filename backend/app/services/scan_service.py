import io
import stat
import zipfile
import tempfile
from pathlib import Path, PurePosixPath
from app.config import settings
from app.models import Scan, ScanStatus, SourceFile, ParseStatus, Function, DocumentationFinding, SeverityLevel, Score
from app.core.parser import ASTCodebaseParser
from app.core.drift_detector import DriftDetector
from app.services.scoring_service import ScoringService

class ScanService:
    @classmethod
    def execute_scan_on_directory(cls, db, scan_id, directory_path):
        scan = db.get(Scan, scan_id)
        try:
            files = ASTCodebaseParser.discover_python_files(directory_path)
            if not files:
                raise ValueError("No Python files found in the upload")
            if len(files) > settings.MAX_ARCHIVE_FILES:
                raise ValueError("Too many Python files")
            total = documented = failed = 0
            findings = []
            severity = {"High": 0, "Medium": 0, "Low": 0}
            for relative, path in files:
                if Path(path).stat().st_size > settings.MAX_FILE_SIZE:
                    raise ValueError("A source file exceeds the 1 MB limit")
                parsed = ASTCodebaseParser.parse_file(relative, path)
                sf = SourceFile(scan_id=scan_id, path=relative, parse_status=ParseStatus(parsed.parse_status),
                                error_message=parsed.error_message)
                db.add(sf)
                db.flush()
                failed += parsed.parse_status == "Failed"
                for func in parsed.functions:
                    total += 1
                    documented += bool(func.docstring and func.docstring.strip())
                    record = Function(file_id=sf.file_id, name=func.name, qualified_name=func.qualified_name,
                                      line_number=func.line_number, signature=func.signature,
                                      docstring=func.docstring, source_code=func.source_code)
                    db.add(record)
                    db.flush()
                    for finding in DriftDetector.analyze_function(func):
                        findings.append(finding)
                        severity[finding.severity] += 1
                        db.add(DocumentationFinding(function_id=record.function_id, type=finding.type,
                                                    severity=SeverityLevel(finding.severity), explanation=finding.explanation))
            score = ScoringService.calculate_drs(total, documented, findings=findings)
            db.add(Score(scan_id=scan_id, programmer_id=scan.initiated_by, **score))
            scan.status = ScanStatus.FAILED if failed == len(files) else (ScanStatus.PARTIAL if failed else ScanStatus.COMPLETED)
            scan.summary = {"total_files": len(files), "parsed_files": len(files)-failed, "failed_files": failed,
                            "total_functions": total, "documented_functions": documented,
                            "undocumented_functions": total-documented, "total_findings": len(findings),
                            "documentation_score": score["documentation_score"], "breakdown": score["breakdown"],
                            **{f"{s.lower()}_severity_findings": n for s, n in severity.items()}}
            db.commit()
            db.refresh(scan)
            return scan
        except Exception:
            db.rollback()
            raise

    @classmethod
    def execute_scan_on_zip(cls, db, scan_id, zip_bytes):
        # Validate every entry before writing; never use extractall on untrusted archives.
        with tempfile.TemporaryDirectory(prefix="intellidoc_") as folder:
            try:
                archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
            except zipfile.BadZipFile:
                raise ValueError("Upload is not a valid ZIP archive")
            with archive:
                entries = archive.infolist()
                if len(entries) > settings.MAX_ARCHIVE_FILES:
                    raise ValueError("Archive has too many entries")
                if sum(i.file_size for i in entries) > settings.MAX_EXPANDED_SIZE:
                    raise ValueError("Expanded archive exceeds 30 MB")
                names = set()
                for item in entries:
                    name = item.filename.replace(chr(92), "/")
                    path = PurePosixPath(name)
                    if path.is_absolute() or ".." in path.parts or ":" in name or stat.S_ISLNK(item.external_attr >> 16):
                        raise ValueError("Archive contains an unsafe path or symbolic link")
                    if item.flag_bits & 1:
                        raise ValueError("Encrypted archives are not supported")
                    if item.is_dir() or path.suffix != ".py" or any(p.startswith(".") or p in ASTCodebaseParser.IGNORED_DIRS for p in path.parts[:-1]):
                        continue
                    if name.casefold() in names:
                        raise ValueError("Archive contains duplicate file names")
                    names.add(name.casefold())
                    if item.file_size > settings.MAX_FILE_SIZE:
                        raise ValueError("A source file exceeds 1 MB")
                    target = Path(folder).joinpath(*path.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        with archive.open(item) as stream:
                            content = stream.read(settings.MAX_FILE_SIZE + 1)
                        if len(content) > settings.MAX_FILE_SIZE:
                            raise ValueError("A source file exceeds 1 MB")
                        target.write_bytes(content)
                    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
                        raise ValueError("Archive is damaged or uses unsupported compression")
            return cls.execute_scan_on_directory(db, scan_id, folder)

