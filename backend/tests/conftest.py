import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
import app.models
from app.database import get_db
from app.main import app
from app.models.user import User, UserRole, Team, Project
from app.models.codebase import Codebase
from app.services.auth_service import AuthService

TEST_DATABASE_URL = "sqlite:///./test_intellidoc.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_users(db_session):
    # Programmer
    prog = User(
        name="Test Programmer",
        email="prog@test.com",
        password_hash=AuthService.hash_password("password123"),
        role=UserRole.PROGRAMMER
    )
    # Team Lead
    lead = User(
        name="Test Team Lead",
        email="lead@test.com",
        password_hash=AuthService.hash_password("password123"),
        role=UserRole.TEAM_LEAD
    )
    # Project Lead
    proj_lead = User(
        name="Test Project Lead",
        email="projlead@test.com",
        password_hash=AuthService.hash_password("password123"),
        role=UserRole.PROJECT_LEAD
    )
    db_session.add_all([prog, lead, proj_lead])
    db_session.flush()

    team = Team(team_name="Engineering Team", team_lead_id=lead.user_id)
    db_session.add(team)
    db_session.flush()

    prog.team_id = team.team_id
    lead.team_id = team.team_id

    project = Project(project_name="Core Project", project_lead_id=proj_lead.user_id)
    db_session.add(project)
    db_session.flush()

    codebase = Codebase(name="Main Repo", owner_id=prog.user_id, project_id=project.project_id)
    db_session.add(codebase)
    db_session.commit()

    return {
        "programmer": prog,
        "team_lead": lead,
        "project_lead": proj_lead,
        "team": team,
        "project": project,
        "codebase": codebase,
    }


@pytest.fixture
def programmer_token(test_users):
    user = test_users["programmer"]
    return AuthService.create_access_token(str(user.user_id), user.email, user.role.value)


@pytest.fixture
def team_lead_token(test_users):
    user = test_users["team_lead"]
    return AuthService.create_access_token(str(user.user_id), user.email, user.role.value)


@pytest.fixture
def project_lead_token(test_users):
    user = test_users["project_lead"]
    return AuthService.create_access_token(str(user.user_id), user.email, user.role.value)

