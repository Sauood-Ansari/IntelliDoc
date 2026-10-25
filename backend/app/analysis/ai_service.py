"""IntelliDoc — AI service abstraction layer.

Supports:
  - Groq (Llama 3.3 70B) for documentation generation
  - Google Gemini Flash for logical-consistency checks
  - Mock mode when API keys are not configured
"""
import httpx
import json
import textwrap
from app.core.config import settings


class AIServiceError(Exception):
    """Raised when an AI service call fails."""
    pass


# ─── Prompt Builders ──────────────────────────────────────────────────────────

def _build_docstring_prompt(func_name: str, params: list[str], body: str) -> str:
    """Build a prompt for Google-style docstring generation."""
    param_list = ", ".join(params) if params else "none"
    # Wrap code in strict XML tags to prevent prompt injection (T-SEC-03)
    return f"""You are a Python documentation expert. Generate a concise, accurate Google-style docstring for the following function.

<code>
def {func_name}({param_list}):
{textwrap.indent(body[:2000], "    ")}
</code>

REQUIREMENTS:
- Use Google-style format with Args: and Returns: sections
- Be accurate to the actual code behavior
- Keep it concise but complete
- Do NOT include the function definition itself
- Output ONLY the docstring content (without triple quotes)

Respond with JSON: {{"docstring": "your docstring here"}}"""


def _build_consistency_prompt(func_name: str, params: list[str], body: str, docstring: str) -> str:
    """Build a prompt for logical-consistency checking."""
    param_list = ", ".join(params) if params else "none"
    return f"""You are a Python code review expert. Analyze whether the following function's documentation is logically consistent with its implementation.

<code>
def {func_name}({param_list}):
{textwrap.indent(body[:2000], "    ")}
</code>

<documentation>
{docstring[:1000]}
</documentation>

Evaluate:
1. Does the description match what the function actually does?
2. Are parameter descriptions accurate?
3. Is the return description accurate?
4. Are there any misleading or incorrect claims?

Respond with JSON: {{
  "verdict": "consistent" | "inconsistent" | "partially_consistent" | "insufficient_info",
  "confidence": "high" | "medium" | "low",
  "issues": ["list of specific issues found, if any"],
  "summary": "one paragraph advisory summary"
}}"""


# ─── Groq Client ──────────────────────────────────────────────────────────────

async def _call_groq(prompt: str) -> str:
    """Call Groq API with Llama 3.3 70B."""
    if not settings.GROQ_API_KEY:
        raise AIServiceError("GROQ_API_KEY not configured")

    async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1024,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ─── Gemini Client ────────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    """Call Google Gemini Flash API."""
    if not settings.GEMINI_API_KEY:
        raise AIServiceError("GEMINI_API_KEY not configured")

    async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


# ─── Mock Responses ───────────────────────────────────────────────────────────

def _mock_docstring(func_name: str, params: list[str]) -> str:
    """Generate a mock docstring for development/demo."""
    param_list = "\n".join(
        f"        {p}: Description of {p}." for p in params
    ) if params else ""
    returns_section = "\n\n    Returns:\n        Result of the operation." if params else ""

    args_section = f"\n\n    Args:\n{param_list}" if param_list else ""
    docstring = f"[MOCK] {func_name} — auto-generated documentation draft.\n\n    This function performs the operation defined in its implementation.{args_section}{returns_section}"
    return json.dumps({"docstring": docstring})


def _mock_consistency(func_name: str) -> str:
    """Generate a mock consistency check result."""
    return json.dumps({
        "verdict": "partially_consistent",
        "confidence": "medium",
        "issues": [
            "[MOCK] This is a placeholder AI result — configure GEMINI_API_KEY for real analysis.",
            f"Function '{func_name}' documentation appears mostly consistent with its implementation."
        ],
        "summary": (
            f"[MOCK MODE] The function '{func_name}' has documentation that appears to broadly describe "
            "its behavior. To get a real analysis, configure the GEMINI_API_KEY environment variable. "
            "This placeholder result should not be used for actual code review decisions."
        )
    })


# ─── Public AI Interface ──────────────────────────────────────────────────────

async def generate_docstring(func_name: str, params: list[str], body: str) -> dict:
    """Generate a draft docstring using Groq (or mock if unavailable).

    Returns:
        dict with keys: docstring, is_mock, provider
    """
    prompt = _build_docstring_prompt(func_name, params, body)

    if not settings.GROQ_API_KEY:
        raw = _mock_docstring(func_name, params)
        data = json.loads(raw)
        return {"docstring": data["docstring"], "is_mock": True, "provider": "mock"}

    try:
        raw = await _call_groq(prompt)
        data = json.loads(raw)
        return {"docstring": data.get("docstring", raw), "is_mock": False, "provider": "groq"}
    except Exception as e:
        raise AIServiceError(f"Groq API error: {str(e)}")


async def check_consistency(
    func_name: str, params: list[str], body: str, docstring: str
) -> dict:
    """Run a logical-consistency check using Gemini (or mock if unavailable).

    Returns:
        dict with keys: verdict, confidence, issues, summary, is_mock, provider
    """
    prompt = _build_consistency_prompt(func_name, params, body, docstring)

    if not settings.GEMINI_API_KEY:
        raw = _mock_consistency(func_name)
        data = json.loads(raw)
        return {**data, "is_mock": True, "provider": "mock"}

    try:
        raw = await _call_gemini(prompt)
        data = json.loads(raw)
        return {**data, "is_mock": False, "provider": "gemini"}
    except Exception as e:
        raise AIServiceError(f"Gemini API error: {str(e)}")
