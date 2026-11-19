"""Exercise the public setup flow and its resource isolation through HTTP."""
from uuid import uuid4

import pytest

from app.models import UserRole
from tests.test_security_and_scans import archive, headers


def signup(client, role, suffix):
    email = f"{suffix}@example.com"
    response = client.post("/api/v1/auth/register", json={
        "name": suffix, "email": email, "password": "ProjectPass123!", "role": role})
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "ProjectPass123!"})
    assert login.status_code == 200
    return headers(login.json()["access_token"])


def organization(client, suffix="one"):
    project_lead = signup(client, "Project Lead", "project-" + suffix)
    team_lead = signup(client, "Team Lead", "team-" + suffix)
    programmer = signup(client, "Programmer", "programmer-" + suffix)
    response = client.post("/api/v1/projects", json={"project_name": "Project " + suffix}, headers=project_lead)
    assert response.status_code == 201, response.text
    project = response.json()
    approve_lead(client, team_lead, project_lead, project["project_id"])
    response = client.post("/api/v1/teams", json={"team_name": "Team " + suffix,
                           "project_id": project["project_id"]}, headers=team_lead)
    assert response.status_code == 201, response.text
    team = response.json()
    approve_programmer(client, programmer, team_lead, team["team_id"])
    response = client.post("/api/v1/codebases", json={"name": "Source", "project_id": project["project_id"],
                           "team_id": team["team_id"]}, headers=programmer)
    assert response.status_code == 201, response.text
    return project_lead, team_lead, programmer, project, team, response.json()


def approve_lead(client, team_lead, project_lead, project_id):
    request = client.post("/api/v1/project-access-requests", json={"project_id": project_id}, headers=team_lead)
    assert request.status_code == 200, request.text
    result = client.patch("/api/v1/project-access-requests/" + request.json()["request_id"],
        json={"decision": "Approve"}, headers=project_lead)
    assert result.status_code == 200, result.text


def approve_programmer(client, programmer, team_lead, team_id):
    request = client.post("/api/v1/team-memberships", json={"team_id": team_id}, headers=programmer)
    assert request.status_code == 200, request.text
    result = client.patch("/api/v1/team-memberships/" + request.json()["membership_id"],
        json={"decision": "Approve"}, headers=team_lead)
    assert result.status_code == 200, result.text


def scan(client, auth, codebase, project_id=None, team_id=None):
    return client.post("/api/v1/scans", headers=auth,
        data={"codebase_id": codebase["codebase_id"], "project_id": project_id or codebase["project_id"],
              "team_id": team_id or codebase["team_id"]},
        files={"file": ("source.zip", archive({"a.py": "def f(): pass"}), "application/zip")})


def test_signup_create_assign_upload_and_review(client):
    pl, tl, programmer, project, team, codebase = organization(client)
    response = scan(client, programmer, codebase)
    assert response.status_code == 201, response.text
    sid = response.json()["scan_id"]
    for lead in (pl, tl):
        assert client.get(f"/api/v1/scans/{sid}/functions", headers=lead).status_code == 200
    assert client.get("/api/v1/project/scores", params={"project_id": project["project_id"]}, headers=pl).json()["teams_count"] == 1
    scores = client.get("/api/v1/team/scores", params={"team_id": team["team_id"]}, headers=tl).json()
    assert scores["programmers_count"] == 1
    assert scores["ranked_programmers"][0]["latest_score"] == 0


def test_wrong_project_team_and_missing_assignments_rejected(client):
    pl, tl, programmer, project, team, codebase = organization(client)
    other = client.post("/api/v1/projects", json={"project_name": "Other project"}, headers=pl).json()
    mismatch = {"name": "Wrong", "project_id": other["project_id"], "team_id": team["team_id"]}
    assert client.post("/api/v1/codebases", json=mismatch, headers=programmer).status_code == 422
    assert scan(client, programmer, codebase, project_id=other["project_id"]).status_code == 422
    assert scan(client, programmer, codebase, team_id=str(uuid4())).status_code == 404
    assert client.post("/api/v1/codebases", json={"name": "Missing assignment"}, headers=programmer).status_code == 422
    assert client.post("/api/v1/scans", data={"codebase_id": codebase["codebase_id"]}, headers=programmer,
        files={"file": ("a.zip", archive({"a.py": "pass"}))}).status_code == 422


def test_saved_assignment_cannot_be_moved_or_leak_across_teams(client):
    pl, tl, programmer, project, team, codebase = organization(client)
    other_pl, other_tl, other_programmer, other_project, other_team, other_cb = organization(client, "two")
    sid = scan(client, programmer, codebase).json()["scan_id"]
    assert client.get(f"/api/v1/scans/{sid}", headers=other_tl).status_code == 404
    assert client.get(f"/api/v1/scans/{sid}", headers=other_pl).status_code == 404
    assert client.get(f"/api/v1/scans/{sid}", headers=other_programmer).status_code == 404
    approve_programmer(client, programmer, other_tl, other_team["team_id"])
    assert scan(client, programmer, codebase, project_id=other_project["project_id"], team_id=other_team["team_id"]).status_code == 409
    assert client.get("/api/v1/team/scores", params={"team_id": team["team_id"]}, headers=other_tl).status_code == 404
    assert client.get("/api/v1/project/scores", params={"project_id": project["project_id"]}, headers=other_pl).status_code == 404
    assert client.get("/api/v1/scans", params={"team_id": team["team_id"]}, headers=other_tl).json() == []
    assert scan(client, other_programmer, codebase).status_code == 404


def test_names_unique_after_normalization_and_lookup_by_id(client):
    pl, tl, programmer, project, team, codebase = organization(client)
    assert client.post("/api/v1/projects", json={"project_name": "  PROJECT   ONE  "}, headers=pl).status_code == 409
    assert client.post("/api/v1/teams", json={"team_name": "TEAM ONE", "project_id": project["project_id"]}, headers=tl).status_code == 409
    assert client.get("/api/v1/projects", params={"search": project["project_id"]}, headers=programmer).json()[0]["project_id"] == project["project_id"]
    assert client.get("/api/v1/teams", params={"search": "team one", "project_id": project["project_id"]}, headers=programmer).json()[0]["team_id"] == team["team_id"]
    assert client.post("/api/v1/projects", json={"project_name": "   "}, headers=pl).status_code == 422


def test_multiple_teams_and_projects_have_explicit_metric_selection(client):
    pl, tl, programmer, project, team, codebase = organization(client)
    project2 = client.post("/api/v1/projects", json={"project_name": "Second"}, headers=pl).json()
    approve_lead(client, tl, pl, project2["project_id"])
    response = client.post("/api/v1/teams", json={"team_name": "Second team", "project_id": project2["project_id"]}, headers=tl)
    assert response.status_code == 201, response.text
    assert len(client.get("/api/v1/teams", params={"owned": True}, headers=tl).json()) == 2
    assert len(client.get("/api/v1/projects", params={"owned": True}, headers=pl).json()) == 2
    assert client.get("/api/v1/team/scores", params={"team_id": response.json()["team_id"]}, headers=tl).status_code == 200
    assert client.get("/api/v1/project/scores", params={"project_id": project2["project_id"]}, headers=pl).status_code == 200


def test_one_programmer_submits_to_multiple_teams_and_projects_without_mixing_results(client):
    pl, tl, programmer, project, team, first = organization(client)
    other_pl, other_tl, _, other_project, other_team, _ = organization(client, "two")
    approve_programmer(client, programmer, other_tl, other_team["team_id"])
    second = client.post("/api/v1/codebases", json={"name": "Second assignment",
        "project_id": other_project["project_id"], "team_id": other_team["team_id"]}, headers=programmer).json()
    approve_lead(client, other_tl, pl, project["project_id"])
    third_team = client.post("/api/v1/teams", json={"team_name": "Another team in first project",
        "project_id": project["project_id"]}, headers=other_tl).json()
    approve_programmer(client, programmer, other_tl, third_team["team_id"])
    third = client.post("/api/v1/codebases", json={"name": "Third assignment",
        "project_id": project["project_id"], "team_id": third_team["team_id"]}, headers=programmer).json()
    first_scan = scan(client, programmer, first).json()["scan_id"]
    third_scan = scan(client, programmer, third).json()["scan_id"]
    response = client.post("/api/v1/scans", headers=programmer,
        data={"codebase_id": second["codebase_id"], "project_id": second["project_id"], "team_id": second["team_id"]},
        files={"file": ("source.zip", archive({"a.py": 'def f():\n    """Documented."""\n    pass'}), "application/zip")})
    assert response.status_code == 201, response.text
    second_scan = response.json()["scan_id"]
    assert len(client.get("/api/v1/codebases", headers=programmer).json()) == 3
    assert len(client.get("/api/v1/scans", headers=programmer).json()) == 3
    for lead, allowed, denied in [(tl, first_scan, second_scan), (other_tl, second_scan, first_scan),
                                  (pl, third_scan, second_scan), (other_pl, second_scan, third_scan)]:
        assert client.get(f"/api/v1/scans/{allowed}", headers=lead).status_code == 200
        assert client.get(f"/api/v1/scans/{denied}", headers=lead).status_code == 404
    for lead, tid, score in [(tl, team["team_id"], 0), (other_tl, other_team["team_id"], 100), (other_tl, third_team["team_id"], 0)]:
        result = client.get("/api/v1/team/scores", params={"team_id": tid}, headers=lead).json()
        assert result["programmers_count"] == (2 if tid == other_team["team_id"] else 1)
        assert result["average_documentation_score"] == score
        assert result["ranked_programmers"][0]["functions_count"] == 1
    first_project = client.get("/api/v1/project/scores", params={"project_id": project["project_id"]}, headers=pl).json()
    assert first_project["teams_count"] == 2
    assert first_project["average_project_score"] == 0
    assert first_project["ranked_programmers"][0]["functions_count"] == 2
    assert sum(row["functions_count"] for row in first_project["ranked_teams"]) == 2
    assert client.get("/api/v1/project/scores", params={"project_id": other_project["project_id"]}, headers=other_pl).json()["average_project_score"] == 100


@pytest.mark.parametrize("role", list(UserRole))
def test_setup_permissions_are_enforced_by_api(client, role):
    auth = signup(client, role.value, role.name.lower())
    result = client.post("/api/v1/projects", json={"project_name": "Roles"}, headers=auth)
    assert result.status_code == (201 if role == UserRole.PROJECT_LEAD else 403)
    if role != UserRole.TEAM_LEAD:
        assert client.post("/api/v1/teams", json={"team_name": "No", "project_id": str(uuid4())}, headers=auth).status_code == 403
    else:
        assert client.post("/api/v1/teams", json={"team_name": "No", "project_id": str(uuid4())}, headers=auth).status_code == 404
