from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from app.models.scan import ScanStatus, ParseStatus


class ScanCreate(BaseModel):
    codebase_id: UUID


class ScanSummary(BaseModel):
    total_files: int = 0
    parsed_files: int = 0
    failed_files: int = 0
    total_functions: int = 0
    documented_functions: int = 0
    undocumented_functions: int = 0
    total_findings: int = 0
    high_severity_findings: int = 0
    medium_severity_findings: int = 0
    low_severity_findings: int = 0
    documentation_score: Optional[float] = None


class SourceFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    file_id: UUID
    path: str
    parse_status: ParseStatus
    error_message: Optional[str] = None


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scan_id: UUID
    codebase_id: UUID
    initiated_by: UUID
    timestamp: datetime
    status: ScanStatus
    summary: Optional[Dict[str, Any]] = None
