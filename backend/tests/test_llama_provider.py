import asyncio
import httpx
import pytest
from app.config import settings
from app.services.ai_service import AIService
from app.services.scoring_service import ScoringService

@pytest.mark.parametrize("kind,task", [("draft","Write only"), ("check","Compare this")])
def test_both_tasks_use_same_groq_model(monkeypatch, kind, task):
    calls = []
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-only-key")
    monkeypatch.setattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return httpx.Response(200, request=httpx.Request("POST", url),
                json={"choices":[{"message":{"content":"Advisory output"}}]})
    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result = asyncio.run(AIService.request(kind, "def f(x): return x"))
    assert result == {"status":"Completed","result":"Advisory output","provider":"Groq"}
    url, payload = calls[0]
    assert url == "https://api.groq.com/openai/v1/chat/completions"
    assert payload["json"]["model"] == "openai/gpt-oss-120b"
    assert payload["json"]["messages"][0]["content"].startswith(task)
    assert payload["json"]["messages"][1]["content"] == "def f(x): return x"

@pytest.mark.parametrize("kind", ["draft","check"])
def test_missing_key_and_context_do_not_send_source(monkeypatch, kind):
    def forbidden(**kwargs): raise AssertionError("Unexpected external request")
    monkeypatch.setattr(httpx, "AsyncClient", forbidden)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    assert asyncio.run(AIService.request(kind, "def f(): pass"))["status"] == "Failed"
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-only-key")
    for source in ["", "x"*(settings.MAX_AI_CONTEXT+1)]:
        assert asyncio.run(AIService.request(kind, source))["status"] == "Failed"

@pytest.mark.parametrize("kind", ["draft","check"])
def test_timeout_returns_safe_failure(monkeypatch, kind):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-only-key")
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, *args, **kwargs): raise httpx.ReadTimeout("private provider detail")
    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result=asyncio.run(AIService.request(kind, "def f(): pass"))
    assert result["status"] == "Failed"
    assert result["provider"] == "Groq"
    assert "private provider detail" not in result["result"]

def test_report_example_matches_implemented_scoring():
    result=ScoringService.calculate_drs(100,80,{"Medium":3})
    assert result["documentation_score"] == 75.2
    assert result["breakdown"]["parameter_consistency"] == 27.2
    assert result["breakdown"]["return_consistency"] == 16

