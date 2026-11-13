from dataclasses import dataclass
from app.core.docstring_parser import GoogleDocstringParser

@dataclass
class DriftFinding:
    type: str
    severity: str
    explanation: str

class DriftDetector:
    @classmethod
    def analyze_function(cls, func):
        if not func.docstring or not func.docstring.strip():
            return [DriftFinding("Missing Documentation", "Low" if func.name.startswith("_") else "High",
                                f"Function '{func.name}' at line {func.line_number} has no docstring.")]
        doc = GoogleDocstringParser.parse(func.docstring)
        actual = {p.lstrip("*") for p in func.parameters}
        if func.receiver:
            actual.discard(func.receiver)
        documented = set(doc.args)
        # Explicitly documenting a receiver is harmless.
        documented.discard(func.receiver)
        result = []
        for p in sorted(actual - documented):
            result.append(DriftFinding("Missing Parameter Documentation", "Medium",
                                      f"Parameter '{p}' exists in the signature but is missing from Args."))
        for p in sorted(documented - actual):
            result.append(DriftFinding("Obsolete Parameter Documentation", "Medium",
                                      f"Parameter '{p}' is documented but absent from the signature."))
        if func.is_generator:
            if not doc.yields:
                result.append(DriftFinding("Missing Yield Documentation", "Low", "This generator yields values but has no Yields section."))
        elif func.has_return_value and not doc.returns:
            result.append(DriftFinding("Missing Return Documentation", "Low",
                                      "A non-None return expression exists, but the Returns section is missing."))
        # No inference about runtime types or whether an expression evaluates to None.
        return result

