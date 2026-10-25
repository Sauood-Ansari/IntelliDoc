"""IntelliDoc — Python AST-based documentation drift analysis engine.

This module implements the core deterministic pipeline:
  1. Source file discovery
  2. AST parsing
  3. Function extraction
  4. Google-style docstring parsing
  5. Documentation drift detection
  6. Score calculation
"""
import ast
import os
import re
import zipfile
import tempfile
import textwrap
from dataclasses import dataclass, field
from typing import Optional
from app.core.config import settings


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class ExtractedParam:
    name: str


@dataclass
class DocstringData:
    raw: str
    documented_params: list[str] = field(default_factory=list)
    has_returns_section: bool = False
    short_description: str = ""


@dataclass
class FunctionMeta:
    name: str
    line_number: int
    params: list[str]          # actual signature params (excluding self/cls)
    has_docstring: bool
    docstring_data: Optional[DocstringData]
    has_return_statement: bool
    source_body: str


@dataclass
class Finding:
    finding_type: str          # matches FindingType enum values
    severity: str              # High | Medium | Low
    explanation: str
    extra: dict = field(default_factory=dict)


@dataclass
class FileAnalysisResult:
    path: str
    parse_status: str          # "ok" | "error"
    parse_error: Optional[str]
    functions: list[FunctionMeta]
    findings_by_function: dict  # function_name -> list[Finding]


@dataclass
class ScanAnalysisResult:
    files: list[FileAnalysisResult]
    total_files: int
    parsed_files: int
    failed_files: int
    total_functions: int
    documented_functions: int
    score: float
    completeness_score: float
    param_consistency_score: float
    return_consistency_score: float


# ─── Algorithm 1: Source File Discovery ────────────────────────────────────────

def discover_python_files(root_path: str) -> tuple[list[str], list[str]]:
    """Recursively find .py files in root_path.

    Returns:
        (python_files, errors): lists of file paths and access errors.
    """
    python_files = []
    errors = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(dirpath, filename)
                if os.access(full_path, os.R_OK):
                    python_files.append(full_path)
                else:
                    errors.append(f"Access denied: {full_path}")
    return python_files, errors


# ─── Algorithm 2 & 3: AST Parsing and Function Extraction ─────────────────────

def _has_return_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if the function has at least one return statement with a value."""
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def _extract_params(args: ast.arguments) -> list[str]:
    """Extract parameter names, excluding 'self' and 'cls'."""
    params = []
    all_args = args.posonlyargs + args.args + args.kwonlyargs
    if args.vararg:
        all_args.append(args.vararg)
    if args.kwarg:
        all_args.append(args.kwarg)
    for arg in all_args:
        if arg.arg not in ("self", "cls"):
            params.append(arg.arg)
    return params


def _get_source_body(source_lines: list[str], node: ast.FunctionDef) -> str:
    """Extract the function source body, dedented."""
    start = node.lineno - 1
    end = node.end_lineno
    body = "".join(source_lines[start:end])
    return textwrap.dedent(body)


def parse_file(file_path: str) -> tuple[Optional[ast.Module], Optional[str], Optional[str]]:
    """Parse a Python source file and return its AST."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
        return tree, source, None
    except SyntaxError as e:
        return None, None, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return None, None, str(e)


# ─── Algorithm 4: Google-Style Docstring Parsing ───────────────────────────────

_GOOGLE_SECTION_RE = re.compile(r"^(?P<section>[A-Za-z][A-Za-z\s]+):\s*$", re.MULTILINE)
_PARAM_RE = re.compile(r"^\s{2,}(?P<name>\*{0,2}\w+)\s*(?:\(.*?\))?\s*:", re.MULTILINE)


def parse_google_docstring(docstring: str) -> DocstringData:
    """Parse a Google-style docstring into structured data."""
    if not docstring:
        return DocstringData(raw="")

    lines = docstring.strip().split("\n")
    short_desc = lines[0].strip() if lines else ""

    documented_params = []
    has_returns = False

    # Split into sections
    sections: dict[str, str] = {}
    current_section = None
    current_content = []

    for line in lines[1:]:
        section_match = _GOOGLE_SECTION_RE.match(line)
        if section_match:
            if current_section:
                sections[current_section] = "\n".join(current_content)
            current_section = section_match.group("section").strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content)

    # Extract args / parameters
    for section_name in ("Args", "Arguments", "Parameters", "Params"):
        if section_name in sections:
            content = sections[section_name]
            for m in _PARAM_RE.finditer(content):
                name = m.group("name").lstrip("*")
                if name and name not in documented_params:
                    documented_params.append(name)
            break

    # Returns section
    for section_name in ("Returns", "Return", "Yields", "Yield"):
        if section_name in sections:
            has_returns = True
            break

    return DocstringData(
        raw=docstring,
        documented_params=documented_params,
        has_returns_section=has_returns,
        short_description=short_desc,
    )


# ─── Algorithm 5 & 6: Drift Detection ─────────────────────────────────────────

def detect_drift(func: FunctionMeta) -> list[Finding]:
    """Apply deterministic drift-detection rules to a function.

    Returns a list of Finding objects.
    """
    findings = []

    if not func.has_docstring:
        findings.append(Finding(
            finding_type="NO_DOCSTRING",
            severity="Medium",
            explanation=(
                f"Function '{func.name}' has no docstring. "
                "Consider adding documentation to describe its purpose, parameters, and return value."
            ),
        ))
        return findings  # No further drift checks possible without a docstring

    doc = func.docstring_data
    sig_params = set(func.params)
    doc_params = set(doc.documented_params)

    # Missing param documentation: in code but not in docs
    missing = sig_params - doc_params
    for param in sorted(missing):
        findings.append(Finding(
            finding_type="MISSING_PARAM_DOC",
            severity="Medium",
            explanation=(
                f"Parameter '{param}' appears in the function signature of '{func.name}' "
                "but is not documented in the docstring."
            ),
            extra={"param": param},
        ))

    # Obsolete param documentation: in docs but not in code
    obsolete = doc_params - sig_params
    for param in sorted(obsolete):
        findings.append(Finding(
            finding_type="OBSOLETE_PARAM_DOC",
            severity="High",
            explanation=(
                f"Parameter '{param}' is documented in the docstring of '{func.name}' "
                "but does not exist in the current function signature. "
                "This may indicate the parameter was removed or renamed."
            ),
            extra={"param": param},
        ))

    # Missing return documentation
    if func.has_return_statement and not doc.has_returns_section:
        findings.append(Finding(
            finding_type="MISSING_RETURN_DOC",
            severity="Low",
            explanation=(
                f"Function '{func.name}' has a return statement but the docstring "
                "does not include a 'Returns:' section."
            ),
        ))

    return findings


# ─── Algorithm 10: Score Calculation ──────────────────────────────────────────

def calculate_score(
    total_functions: int,
    documented_functions: int,
    all_findings: list[Finding],
) -> tuple[float, float, float, float]:
    """Calculate the Documentation Reliability Score.

    Returns:
        (total_score, completeness, param_consistency, return_consistency)
    """
    if total_functions == 0:
        return 0.0, 0.0, 0.0, 0.0

    completeness = settings.COMPLETENESS_MAX * (documented_functions / total_functions)

    param_penalty = 0.0
    return_penalty = 0.0

    for f in all_findings:
        if f.finding_type == "MISSING_PARAM_DOC":
            param_penalty += settings.PENALTY_MISSING_PARAM
        elif f.finding_type == "OBSOLETE_PARAM_DOC":
            param_penalty += settings.PENALTY_OBSOLETE_PARAM
        elif f.finding_type == "MISSING_RETURN_DOC":
            return_penalty += settings.PENALTY_MISSING_RETURN

    param_consistency = max(0.0, settings.PARAM_CONSISTENCY_MAX - param_penalty)
    return_consistency = max(0.0, settings.RETURN_CONSISTENCY_MAX - return_penalty)

    total = min(100.0, max(0.0, completeness + param_consistency + return_consistency))
    return total, completeness, param_consistency, return_consistency


# ─── Main Analysis Pipeline ────────────────────────────────────────────────────

def analyse_file(file_path: str, root_path: str) -> FileAnalysisResult:
    """Parse and analyse a single Python source file."""
    relative_path = os.path.relpath(file_path, root_path)

    tree, source, error = parse_file(file_path)
    if error:
        return FileAnalysisResult(
            path=relative_path,
            parse_status="error",
            parse_error=error,
            functions=[],
            findings_by_function={},
        )

    source_lines = source.splitlines(keepends=True)
    functions = []
    findings_by_function = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = _extract_params(node.args)
            docstring_raw = ast.get_docstring(node)
            has_docstring = docstring_raw is not None
            docstring_data = parse_google_docstring(docstring_raw) if has_docstring else None

            try:
                body = _get_source_body(source_lines, node)
            except Exception:
                body = ""

            func = FunctionMeta(
                name=node.name,
                line_number=node.lineno,
                params=params,
                has_docstring=has_docstring,
                docstring_data=docstring_data,
                has_return_statement=_has_return_value(node),
                source_body=body[:settings.MAX_AI_CONTEXT_CHARS],  # Truncate for AI safety
            )
            functions.append(func)
            findings = detect_drift(func)
            if findings:
                findings_by_function[func.name] = findings

    return FileAnalysisResult(
        path=relative_path,
        parse_status="ok",
        parse_error=None,
        functions=functions,
        findings_by_function=findings_by_function,
    )


def analyse_codebase(root_path: str) -> ScanAnalysisResult:
    """Run the full deterministic analysis pipeline on a codebase directory."""
    python_files, file_errors = discover_python_files(root_path)

    file_results = []
    total_functions = 0
    documented_functions = 0
    all_findings = []
    failed_files = len(file_errors)

    for fp in python_files:
        result = analyse_file(fp, root_path)
        file_results.append(result)

        if result.parse_status == "error":
            failed_files += 1
        else:
            for func in result.functions:
                total_functions += 1
                if func.has_docstring:
                    documented_functions += 1
            for findings in result.findings_by_function.values():
                all_findings.extend(findings)

    # Add placeholder results for access errors
    for err in file_errors:
        file_results.append(FileAnalysisResult(
            path=err,
            parse_status="error",
            parse_error="File access denied",
            functions=[],
            findings_by_function={},
        ))

    total, completeness, param_cons, return_cons = calculate_score(
        total_functions, documented_functions, all_findings
    )

    parsed_files = len(python_files) - (failed_files - len(file_errors))

    return ScanAnalysisResult(
        files=file_results,
        total_files=len(python_files),
        parsed_files=parsed_files,
        failed_files=failed_files,
        total_functions=total_functions,
        documented_functions=documented_functions,
        score=total,
        completeness_score=completeness,
        param_consistency_score=param_cons,
        return_consistency_score=return_cons,
    )


# ─── Secure Archive Extraction (T-SEC-02 Defense) ─────────────────────────────

class SecurityError(Exception):
    pass


def safe_extract_archive(zip_path: str, target_dir: str) -> list[str]:
    """Extract a ZIP archive, defending against Zip Slip attacks.

    Only .py files are extracted.
    """
    extracted_files = []
    base_dir = os.path.abspath(target_dir)
    with zipfile.ZipFile(zip_path, "r") as archive:
        # Check size
        total_size = sum(i.file_size for i in archive.infolist())
        max_bytes = settings.MAX_SOURCE_SIZE_MB * 1024 * 1024
        if total_size > max_bytes:
            raise ValueError(f"Archive uncompressed size exceeds {settings.MAX_SOURCE_SIZE_MB} MB limit")

        for member in archive.infolist():
            target_path = os.path.abspath(os.path.join(base_dir, member.filename))
            if not target_path.startswith(base_dir + os.sep):
                raise SecurityError(f"Zip Slip attack attempt detected: {member.filename}")
            if not member.is_dir() and member.filename.endswith(".py"):
                archive.extract(member, base_dir)
                extracted_files.append(target_path)
    return extracted_files
