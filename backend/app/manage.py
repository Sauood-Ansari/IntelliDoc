"""Trusted administrator CLI. Role and membership changes are never public API actions."""
import argparse
import getpass
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import User, Team, Project, Codebase, UserRole
from app.services.auth_service import AuthService

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    users = commands.add_parser("add-user")
    users.add_argument("--name", required=True)
    users.add_argument("--email", required=True)
    users.add_argument("--role", choices=[r.value for r in UserRole], default="Programmer")
    users.add_argument("--team")
    team = commands.add_parser("add-team")
    team.add_argument("--name", required=True)
    team.add_argument("--lead-email", required=True)
    project = commands.add_parser("add-project")
    project.add_argument("--name", required=True)
    project.add_argument("--lead-email", required=True)
    assign = commands.add_parser("assign-user")
    assign.add_argument("--email", required=True)
    assign.add_argument("--team", required=True)
    link = commands.add_parser("assign-codebase")
    link.add_argument("--codebase", required=True)
    link.add_argument("--project", required=True)
    commands.add_parser("list")
    args = parser.parse_args()
    with SessionLocal() as db:
        def user(email):
            found = db.query(User).filter(User.email == email.lower()).first()
            if not found:
                raise ValueError("User does not exist")
            return found
        try:
            if args.command == "list":
                for u in db.query(User).all():
                    print(f"User: {u.email} | {u.role.value} | team={u.team_id}")
                for t in db.query(Team).all():
                    print(f"Team: {t.team_id} | {t.team_name}")
                for p in db.query(Project).all():
                    print(f"Project: {p.project_id} | {p.project_name}")
                for c in db.query(Codebase).all():
                    print(f"Codebase: {c.codebase_id} | {c.name} | project={c.project_id}")
                return
            if args.command == "add-user":
                from pydantic import TypeAdapter, EmailStr
                email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
                if not args.name.strip() or len(args.name) > 100:
                    raise ValueError("Name must contain 1–100 characters")
                password = getpass.getpass("Password (at least 10 characters): ")
                if len(password) < 10 or len(password.encode()) > 72:
                    raise ValueError("Use at least 10 characters and at most 72 UTF-8 bytes")
                team_id = UUID(args.team) if args.team else None
                if team_id and not db.get(Team, team_id):
                    raise ValueError("Team does not exist")
                record = User(name=args.name, email=email, role=UserRole(args.role), team_id=team_id,
                              password_hash=AuthService.hash_password(password))
                db.add(record)
            elif args.command == "add-team":
                lead = user(args.lead_email)
                if lead.role != UserRole.TEAM_LEAD:
                    raise ValueError("Team leader must have Team Lead role")
                if not args.name.strip() or len(args.name) > 100:
                    raise ValueError("Team name must contain 1–100 characters")
                record = Team(team_name=args.name, team_lead_id=lead.user_id)
                db.add(record)
                db.flush()
                lead.team_id = record.team_id
            elif args.command == "add-project":
                lead = user(args.lead_email)
                if lead.role != UserRole.PROJECT_LEAD:
                    raise ValueError("Project leader must have Project Lead role")
                if not args.name.strip() or len(args.name) > 150:
                    raise ValueError("Project name must contain 1–150 characters")
                db.add(Project(project_name=args.name, project_lead_id=lead.user_id))
            elif args.command == "assign-user":
                member = user(args.email)
                team = db.get(Team, UUID(args.team))
                if not team or member.role != UserRole.PROGRAMMER:
                    raise ValueError("Assign a Programmer to an existing team")
                member.team_id = team.team_id
            else:
                codebase = db.get(Codebase, UUID(args.codebase))
                project = db.get(Project, UUID(args.project))
                if not codebase or not project:
                    raise ValueError("Codebase or project does not exist")
                codebase.project_id = project.project_id
            db.commit()
            print("Saved. Use 'python -m app.manage list' to inspect assignments.")
        except (ValueError, IntegrityError) as exc:
            db.rollback()
            parser.exit(1, "Unable to save: check input, unique email/team names, and existing assignments.\n")

if __name__ == "__main__":
    main()

