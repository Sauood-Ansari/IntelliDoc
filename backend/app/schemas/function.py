from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.function import SeverityLevel


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    finding_id: UUID
    function_id: UUID
    type: str
    severity: SeverityLevel
    explanation: str


class FunctionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    function_id: UUID
    file_id: UUID
    name: str
    line_number: int
    signature: str
    docstring: Optional[str] = None
    has_docstring: bool = False


class FunctionDetailOut(FunctionOut):
    file_path: Optional[str] = None
    source_code: str = ""
    qualified_name: str = ""
    findings: List[FindingOut] = []
