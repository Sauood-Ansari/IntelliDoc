"""The organization migration must support old data and fresh installations."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import uuid4


def migrate(path):
    environment = {**os.environ, "DATABASE_URL": "sqlite:///" + str(path).replace("\\", "/")}
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[1], env=environment, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr


def test_fresh_schema_reaches_new_revision(tmp_path):
    path = tmp_path / "fresh.db"
    migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0003"
        assert "team_id" in {row[1] for row in db.execute("PRAGMA table_info(codebases)")}
        assert "project_id" in {row[1] for row in db.execute("PRAGMA table_info(teams)")}
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_legacy_assignment_backfilled_without_losing_records(tmp_path):
    path = tmp_path / "legacy.db"
    programmer, lead, project_lead, team, project, codebase = [uuid4().hex for _ in range(6)]
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE users (user_id CHAR(32) PRIMARY KEY, name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(12) NOT NULL, team_id CHAR(32) REFERENCES teams(team_id), created_at DATETIME);
            CREATE TABLE teams (team_id CHAR(32) PRIMARY KEY, team_name VARCHAR(100) UNIQUE NOT NULL,
                team_lead_id CHAR(32) UNIQUE REFERENCES users(user_id));
            CREATE TABLE projects (project_id CHAR(32) PRIMARY KEY, project_name VARCHAR(150) NOT NULL,
                project_lead_id CHAR(32) NOT NULL REFERENCES users(user_id));
            CREATE TABLE codebases (codebase_id CHAR(32) PRIMARY KEY, name VARCHAR(150) NOT NULL,
                owner_id CHAR(32) NOT NULL REFERENCES users(user_id), project_id CHAR(32) REFERENCES projects(project_id));
            CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY);
            INSERT INTO alembic_version VALUES ('0001');
        """)
        for id_, name, role, member_team in ((programmer, "Student", "PROGRAMMER", team),
            (lead, "Team Lead", "TEAM_LEAD", team), (project_lead, "Project Lead", "PROJECT_LEAD", None)):
            db.execute("INSERT INTO users VALUES (?, ?, ?, 'hash', ?, ?, NULL)", (id_, name, id_ + "@example.com", role, member_team))
        db.execute("INSERT INTO teams VALUES (?, 'Team Alpha', ?)", (team, lead))
        db.execute("INSERT INTO projects VALUES (?, 'University', ?)", (project, project_lead))
        db.execute("INSERT INTO codebases VALUES (?, 'Submission', ?, ?)", (codebase, programmer, project))
    migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT team_id FROM codebases WHERE codebase_id=?", (codebase,)).fetchone()[0] == team
        assert db.execute("SELECT project_id, name_key FROM teams WHERE team_id=?", (team,)).fetchone() == (project, "team alpha")
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 3
        assert db.execute("SELECT status, decided_by FROM project_access_requests").fetchone() == ("APPROVED", project_lead)
        assert db.execute("SELECT status, decided_by FROM team_memberships").fetchone() == ("APPROVED", lead)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        # One lead can create another team after removing the old unique constraint.
        db.execute("INSERT INTO teams (team_id, team_name, name_key, team_lead_id, project_id) VALUES (?, 'Second', 'second', ?, ?)",
                   (uuid4().hex, lead, project))
