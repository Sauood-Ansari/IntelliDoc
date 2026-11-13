import io
import zipfile
from uuid import uuid4
import pytest
from app.models import User, UserRole, Team, Project, Codebase, AIAnalysis, AIAnalysisType, AIAnalysisStatus
from app.services.auth_service import AuthService
from app.config import settings

def headers(token):
    return {"Authorization": "Bearer " + token}

def archive(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, source in files.items():
            z.writestr(name, source)
    return buffer.getvalue()

def upload(client, token, codebase, files):
    return client.post("/api/v1/scans", data={"codebase_id": str(codebase.codebase_id)},
                       files={"file": ("source.zip", archive(files), "application/zip")}, headers=headers(token))

def test_scan_persists_source_findings_and_errors(client, test_users, programmer_token):
    result = upload(client, programmer_token, test_users["codebase"], {
        "valid.py": 'def price(base, tax):\n    """Price.\n\n    Args:\n        base: Base price.\n    """\n    return base + tax\n',
        "broken.py": "def broken(:\n"
    })
    assert result.status_code == 201, result.text
    scan = result.json()
    assert scan["status"] == "Partial"
    assert scan["summary"]["total_functions"] == 1
    assert scan["summary"]["total_findings"] == 2
    sid = scan["scan_id"]
    files = client.get(f"/api/v1/scans/{sid}/files", headers=headers(programmer_token)).json()
    assert any(f["error_message"] and "SyntaxError" in f["error_message"] for f in files)
    funcs = client.get(f"/api/v1/scans/{sid}/functions", headers=headers(programmer_token)).json()
    assert "return base + tax" in funcs[0]["source_code"]
    assert funcs[0]["file_path"] == "valid.py"
    assert len(funcs[0]["findings"]) == 2
    assert scan["summary"]["breakdown"]["parameter_consistency"] == 38
    assert scan["summary"]["breakdown"]["return_consistency"] == 19

@pytest.mark.parametrize("path", ["../escape.py", "/absolute.py", "C:/outside.py", "a/../../outside.py", "..\\escape.py"])
def test_archive_rejects_unsafe_paths(client, test_users, programmer_token, path):
    response = upload(client, programmer_token, test_users["codebase"], {path: "def f(): pass"})
    assert response.status_code == 400
    assert client.get("/api/v1/scans", headers=headers(programmer_token)).json()[0]["status"] == "Failed"

def test_invalid_archive_and_no_python(client, test_users, programmer_token):
    response = client.post("/api/v1/scans", data={"codebase_id":str(test_users["codebase"].codebase_id)},
                           files={"file":("bad.zip",b"not a zip")},headers=headers(programmer_token))
    assert response.status_code == 400
    assert upload(client, programmer_token, test_users["codebase"], {"readme.md":"hello"}).status_code == 400

def test_upload_limits(client, test_users, programmer_token, monkeypatch):
    monkeypatch.setattr(settings,"MAX_SOURCE_SIZE",20)
    assert upload(client, programmer_token, test_users["codebase"], {"a.py":"def f(): pass"}).status_code == 413

def test_expansion_and_entry_limits(client, test_users, programmer_token, monkeypatch):
    monkeypatch.setattr(settings,"MAX_EXPANDED_SIZE",10)
    assert upload(client, programmer_token, test_users["codebase"], {"a.py":"def f(): return 1234"}).status_code == 400
    monkeypatch.setattr(settings,"MAX_EXPANDED_SIZE",1000)
    monkeypatch.setattr(settings,"MAX_ARCHIVE_FILES",1)
    assert upload(client, programmer_token, test_users["codebase"], {"a.py":"pass","b.py":"pass"}).status_code == 400

def test_empty_scan_is_not_applicable(client,test_users,programmer_token):
    result=upload(client,programmer_token,test_users["codebase"],{"empty.py":"x = 1"})
    assert result.status_code==201
    assert result.json()["summary"]["documentation_score"] is None

@pytest.mark.parametrize("role",list(UserRole))
def test_cross_scope_denied_everywhere(client,db_session,test_users,programmer_token,role):
    result=upload(client,programmer_token,test_users["codebase"],{"a.py":"def f(x): return x"})
    sid=result.json()["scan_id"]
    fid=client.get(f"/api/v1/scans/{sid}/functions",headers=headers(programmer_token)).json()[0]["function_id"]
    stranger=User(name="Other",email=f"{role.name.lower()}@other.test",role=role,
                  password_hash=AuthService.hash_password("otherpassword"))
    db_session.add(stranger);db_session.commit()
    token=AuthService.create_access_token(str(stranger.user_id),stranger.email,stranger.role.value)
    for endpoint in [f"/scans/{sid}",f"/scans/{sid}/functions",f"/scans/{sid}/files",f"/scans/{sid}/findings",
                     f"/functions/{fid}",f"/functions/{fid}/analyses"]:
        assert client.get("/api/v1"+endpoint,headers=headers(token)).status_code==404, endpoint
    assert client.get("/api/v1/scans",headers=headers(token)).json()==[]
    assert client.get("/api/v1/codebases",headers=headers(token)).json()==[]
    assert client.post(f"/api/v1/functions/{fid}/generate-doc",headers=headers(token)).status_code in (403,404)

def test_project_no_fallback(client,db_session,test_users):
    stranger=User(name="Unassigned",email="unassigned@test.com",role=UserRole.PROJECT_LEAD,password_hash="unused")
    db_session.add(stranger);db_session.commit()
    token=AuthService.create_access_token(str(stranger.user_id),stranger.email,stranger.role.value)
    assert client.get("/api/v1/project/scores",headers=headers(token)).status_code==404

def test_public_registration_cannot_escalate(client):
    response=client.post("/api/v1/auth/register",json={"name":"Escalation","email":"new@test.com","password":"longpassword","role":"Project Lead"})
    assert response.status_code==403

def test_no_server_directory_scanning(client,test_users,programmer_token):
    response=client.post("/api/v1/scans",data={"codebase_id":str(test_users["codebase"].codebase_id),"directory_path":"C:/"},
                         headers=headers(programmer_token))
    assert response.status_code==422

def test_ai_failure_and_review_do_not_change_scan(client,test_users,programmer_token,monkeypatch):
    monkeypatch.setattr(settings,"GROQ_API_KEY","")
    result=upload(client,programmer_token,test_users["codebase"],{"a.py":"def f(x): return x"})
    sid=result.json()["scan_id"]
    fid=client.get(f"/api/v1/scans/{sid}/functions",headers=headers(programmer_token)).json()[0]["function_id"]
    response=client.post(f"/api/v1/functions/{fid}/generate-doc",headers=headers(programmer_token))
    assert response.status_code==200
    assert response.json()["status"]=="Failed"
    from app.services.ai_service import AIService
    async def fake(kind, source):
        assert "return x" in source
        return {"status":"Completed","provider":"Test provider","result":"A draft"}
    monkeypatch.setattr(AIService,"request",fake)
    response=client.post(f"/api/v1/functions/{fid}/generate-doc",headers=headers(programmer_token))
    aid=response.json()["analysis_id"]
    reviewed=client.patch(f"/api/v1/functions/{fid}/analyses/{aid}",json={"decision":"Accepted","edited_text":"Reviewed draft"},
                          headers=headers(programmer_token))
    assert reviewed.status_code==200
    assert reviewed.json()["reviewed_text"]=="Reviewed draft"
    assert client.get(f"/api/v1/scans/{sid}",headers=headers(programmer_token)).json()["summary"]==result.json()["summary"]

