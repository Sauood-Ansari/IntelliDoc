import inspect
import re
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ParsedDocstring:
    summary: str = ""
    args: dict[str, str] = field(default_factory=dict)
    returns: Optional[str] = None
    yields: Optional[str] = None
    raises: list[str] = field(default_factory=list)
    raw_docstring: str = ""

class GoogleDocstringParser:
    @classmethod
    def parse(cls, docstring):
        if not docstring or not docstring.strip():
            return None
        text = inspect.cleandoc(docstring)
        parsed = ParsedDocstring(raw_docstring=text)
        section, current, arg_indent = "summary", None, None
        sections = {"Args": "args", "Arguments": "args", "Parameters": "args",
                    "Returns": "returns", "Return": "returns", "Yields": "yields", "Raises": "raises"}
        for line in text.splitlines():
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            if indent == 0 and re.fullmatch(r"[A-Za-z][A-Za-z ]*:", stripped):
                section = sections.get(stripped[:-1], "other")
                current, arg_indent = None, None
                continue
            if not stripped:
                continue
            if section == "summary":
                parsed.summary = (parsed.summary + " " + stripped).strip()
            elif section == "args":
                match = re.match(r"(\*{0,2}[A-Za-z_]\w*)\s*(?:\([^)]*\))?\s*:\s*(.*)", stripped)
                if match and (arg_indent is None or indent == arg_indent):
                    current, description = match.groups()
                    current = current.lstrip("*")
                    parsed.args[current] = description
                    arg_indent = indent
                elif current and indent > arg_indent:
                    parsed.args[current] += " " + stripped
            elif section in ("returns", "yields"):
                setattr(parsed, section, ((getattr(parsed, section) or "") + " " + stripped).strip())
            elif section == "raises":
                parsed.raises.append(stripped)
        return parsed

