import uuid
from app.database import SessionLocal, engine
from app.models.base import Base
import app.models
from app.models.user import User, Team, Project, UserRole
from app.models.codebase import Codebase
from app.services.auth_service import AuthService


def seed_database():
    """
    Populates initial test accounts for all 3 user roles, team, project, and codebase.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already has records. Skipping seed.")
            return

        print("Seeding database with demo university records...")

        # 1. Create Project Lead
        project_lead = User(
            user_id=uuid.uuid4(),
            name="Demo Project Lead",
            email="projectlead@intellidoc.edu",
            password_hash=AuthService.hash_password("LeadPass123!"),
            role=UserRole.PROJECT_LEAD
        )
        db.add(project_lead)
        db.flush()

        # 2. Create Project
        project = Project(
            project_id=uuid.uuid4(),
            project_name="IntelliDoc University Project",
            project_lead_id=project_lead.user_id
        )
        db.add(project)
        db.flush()

        # 3. Create Team Lead
        team_lead = User(
            user_id=uuid.uuid4(),
            name="Demo Team Lead",
            email="teamlead@intellidoc.edu",
            password_hash=AuthService.hash_password("TeamPass123!"),
            role=UserRole.TEAM_LEAD
        )
        db.add(team_lead)
        db.flush()

        # 4. Create Team
        team = Team(
            team_id=uuid.uuid4(),
            team_name="Team Alpha",
            team_lead_id=team_lead.user_id
        )
        db.add(team)
        db.flush()

        # Update Team Lead's team_id
        team_lead.team_id = team.team_id

        # 5. Create Programmers
        prog1 = User(
            user_id=uuid.uuid4(),
            name="Sauood Ansari",
            email="sauood@intellidoc.edu",
            password_hash=AuthService.hash_password("ProgPass123!"),
            role=UserRole.PROGRAMMER,
            team_id=team.team_id
        )
        prog2 = User(
            user_id=uuid.uuid4(),
            name="Alice Smith",
            email="alice@intellidoc.edu",
            password_hash=AuthService.hash_password("ProgPass123!"),
            role=UserRole.PROGRAMMER,
            team_id=team.team_id
        )
        db.add_all([prog1, prog2])
        db.flush()

        # 6. Create Codebase
        codebase = Codebase(
            codebase_id=uuid.uuid4(),
            name="IntelliDoc Sample Codebase",
            owner_id=prog1.user_id,
            project_id=project.project_id
        )
        db.add(codebase)

        db.commit()
        from pathlib import Path
        from app.models.scan import Scan, ScanStatus
        from app.services.scan_service import ScanService
        sample = Path(__file__).resolve().parents[2] / "samples" / "student_api"
        if sample.exists():
            scan = Scan(codebase_id=codebase.codebase_id, initiated_by=prog1.user_id, status=ScanStatus.RUNNING)
            db.add(scan)
            db.commit()
            ScanService.execute_scan_on_directory(db, scan.scan_id, str(sample))
        print("Database seeded successfully!")
        print("Accounts created:")
        print("  - Project Lead: projectlead@intellidoc.edu / LeadPass123!")
        print("  - Team Lead:    teamlead@intellidoc.edu / TeamPass123!")
        print("  - Programmer:   sauood@intellidoc.edu / ProgPass123!")
        print("  - Programmer:   alice@intellidoc.edu / ProgPass123!")

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

