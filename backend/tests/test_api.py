from fastapi import status


def test_auth_login_success(client, test_users):
    # T-01: Valid login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "prog@test.com", "password": "password123"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "Programmer"
    assert data["token_type"] == "bearer"


def test_auth_login_invalid(client, test_users):
    # T-01: Invalid login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "prog@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_no_token(client):
    # T-02: Protected endpoint without token
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_codebase_programmer(client, programmer_token):
    # T-03: Register codebase
    response = client.post(
        "/api/v1/codebases",
        json={"name": "New Codebase"},
        headers={"Authorization": f"Bearer {programmer_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Codebase"


def test_programmer_dashboard_me(client, programmer_token):
    # T-17: Programmer metrics dashboard
    response = client.get(
        "/api/v1/scores/me",
        headers={"Authorization": f"Bearer {programmer_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "scores" in data
    assert data["email"] == "prog@test.com"


def test_team_lead_dashboard_as_team_lead(client, team_lead_token):
    # T-18: Team Lead can access team dashboard
    response = client.get(
        "/api/v1/team/scores",
        headers={"Authorization": f"Bearer {team_lead_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "ranked_programmers" in data


def test_team_lead_dashboard_denied_to_programmer(client, programmer_token):
    # T-18: Programmer is denied access to Team Lead dashboard
    response = client.get(
        "/api/v1/team/scores",
        headers={"Authorization": f"Bearer {programmer_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_project_lead_dashboard_as_project_lead(client, project_lead_token):
    # T-19: Project Lead can access project dashboard
    response = client.get(
        "/api/v1/project/scores",
        headers={"Authorization": f"Bearer {project_lead_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "ranked_teams" in data


def test_project_lead_dashboard_denied_to_team_lead(client, team_lead_token):
    # T-19: Team Lead is denied access to Project Lead dashboard
    response = client.get(
        "/api/v1/project/scores",
        headers={"Authorization": f"Bearer {team_lead_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

