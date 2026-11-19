from tests.test_organization_workflow import signup, organization


def test_team_creation_requires_responsible_project_lead_approval(client):
    pl = signup(client, "Project Lead", "owner")
    outsider = signup(client, "Project Lead", "outsider")
    tl = signup(client, "Team Lead", "requester")
    project = client.post("/api/v1/projects", headers=pl, json={"project_name": "Approval project"}).json()
    body = {"team_name": "Approval team", "project_id": project["project_id"]}
    assert client.post("/api/v1/teams", headers=tl, json=body).status_code == 403
    assert client.get("/api/v1/projects?eligible=true", headers=tl).json() == []
    request = client.post("/api/v1/project-access-requests", headers=tl, json={"project_id": project["project_id"]}).json()
    route = "/api/v1/project-access-requests/" + request["request_id"]
    assert request["status"] == "Pending"
    assert client.patch(route, headers=outsider, json={"decision": "Approve"}).status_code == 404
    assert client.patch(route, headers=tl, json={"decision": "Approve"}).status_code == 403
    assert client.patch(route, headers=pl, json={"decision": "Approve"}).json()["status"] == "Approved"
    assert len(client.get("/api/v1/projects?eligible=true", headers=tl).json()) == 1
    assert client.post("/api/v1/teams", headers=tl, json=body).status_code == 201


def test_programmer_requires_only_responsible_team_lead_approval(client):
    pl, tl, _, project, team, _ = organization(client)
    prog = signup(client, "Programmer", "new-member")
    other_tl = signup(client, "Team Lead", "unrelated-lead")
    body = {"name": "New", "project_id": project["project_id"], "team_id": team["team_id"]}
    assert client.post("/api/v1/codebases", headers=prog, json=body).status_code == 403
    assert client.get("/api/v1/teams?eligible=true", headers=prog).json() == []
    request = client.post("/api/v1/team-memberships", headers=prog, json={"team_id": team["team_id"]}).json()
    route = "/api/v1/team-memberships/" + request["membership_id"]
    assert request["status"] == "Pending"
    assert client.post("/api/v1/codebases", headers=prog, json=body).status_code == 403
    for auth, status in [(pl,403),(other_tl,404),(prog,403)]:
        assert client.patch(route, headers=auth, json={"decision": "Approve"}).status_code == status
    assert client.patch(route, headers=tl, json={"decision": "Approve"}).json()["status"] == "Approved"
    assert client.post("/api/v1/codebases", headers=prog, json=body).status_code == 201
    assert len(client.get("/api/v1/teams?eligible=true", headers=prog).json()) == 1
    assert len(client.get("/api/v1/projects?eligible=true", headers=prog).json()) == 1
    scores = client.get("/api/v1/project/scores", headers=pl, params={"project_id": project["project_id"]}).json()
    member = next(row for row in scores["ranked_programmers"] if row["email"] == "new-member@example.com")
    assert member["latest_score"] is None and member["functions_count"] == 0


def test_rejection_retry_and_request_visibility(client):
    pl, tl, _, project, team, _ = organization(client)
    other_pl, other_tl, _, other_project, other_team, _ = organization(client,"other")
    prog = signup(client, "Programmer", "retry-member")
    body = {"team_id": team["team_id"]}
    first = client.post("/api/v1/team-memberships", headers=prog, json=body).json()
    assert client.post("/api/v1/team-memberships", headers=prog, json=body).json()["membership_id"] == first["membership_id"]
    route = "/api/v1/team-memberships/" + first["membership_id"]
    rejected = client.patch(route, headers=tl, json={"decision": "Reject", "note": "Confirm your team."}).json()
    assert rejected["status"] == "Rejected" and rejected["decision_note"] == "Confirm your team."
    assert client.patch(route, headers=tl, json={"decision": "Approve"}).status_code == 409
    retry = client.post("/api/v1/team-memberships", headers=prog, json=body).json()
    assert retry["membership_id"] == first["membership_id"] and retry["status"] == "Pending"
    assert retry["decided_by"] is None and retry["decision_note"] is None
    assert client.patch(route, headers=tl, json={"decision": "Approve"}).json()["status"] == "Approved"
    assert len(client.get("/api/v1/team-memberships", headers=prog).json()) == 1
    assert all(row["project_id"] == other_project["project_id"] for row in client.get("/api/v1/team-memberships", headers=other_pl).json())
    assert all(row["team_id"] == other_team["team_id"] for row in client.get("/api/v1/team-memberships", headers=other_tl).json())
    assert client.get("/api/v1/project-access-requests", headers=prog).status_code == 403
