#!/usr/bin/env python3
"""IntelliDoc — Database seeder for development and demo.

Creates sample users, teams, projects, and scans with realistic data.

Usage:
    cd backend && .venv/bin/python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, create_tables
from app.core.security import hash_password
from app.models.models import (
    User, UserRole, Team, Project, Scan, ScanStatus, Score,
    SourceFile, Function, DocumentationFinding, FindingType, FindingSeverity
)
from datetime import datetime, timezone, timedelta
import random


def seed():
    print("🌱 Seeding IntelliDoc database...")
    create_tables()
    db = SessionLocal()

    try:
        # Clean existing data
        for model in [Score, DocumentationFinding, Function, SourceFile, Scan, User, Team, Project]:
            db.query(model).delete()
        db.commit()

        # ── Project Lead ────────────────────────────────────────────────────
        lead = User(
            name="Prof. Aasim Zafar",
            email="lead@intellidoc.dev",
            password_hash=hash_password("password123"),
            role=UserRole.project_lead,
        )
        db.add(lead)
        db.flush()

        project = Project(
            name="AMU MCA Software Lab",
            description="Final year MCA student projects at Aligarh Muslim University",
            project_lead_id=lead.id,
        )
        db.add(project)
        db.flush()

        # ── Teams ─────────────────────────────────────────────────────────────
        tl1 = User(
            name="Mr. Kausar Ali",
            email="tl1@intellidoc.dev",
            password_hash=hash_password("password123"),
            role=UserRole.team_lead,
        )
        tl2 = User(
            name="Mr. Mohd Adnan",
            email="tl2@intellidoc.dev",
            password_hash=hash_password("password123"),
            role=UserRole.team_lead,
        )
        db.add_all([tl1, tl2])
        db.flush()

        team_a = Team(name="Team Alpha — Backend", project_id=project.id, team_lead_id=tl1.id)
        team_b = Team(name="Team Beta — Frontend", project_id=project.id, team_lead_id=tl2.id)
        db.add_all([team_a, team_b])
        db.flush()

        tl1.team_id = team_a.id
        tl2.team_id = team_b.id

        # ── Programmers ───────────────────────────────────────────────────────
        programmers_data = [
            ("Sauood Ansari", "sauood@intellidoc.dev", team_a.id),
            ("Rahul Sharma", "rahul@intellidoc.dev", team_a.id),
            ("Priya Gupta", "priya@intellidoc.dev", team_a.id),
            ("Aisha Khan", "aisha@intellidoc.dev", team_b.id),
            ("Dev Patel", "dev@intellidoc.dev", team_b.id),
            ("Nisha Singh", "nisha@intellidoc.dev", team_b.id),
        ]

        programmers = []
        for name, email, team_id in programmers_data:
            p = User(
                name=name,
                email=email,
                password_hash=hash_password("password123"),
                role=UserRole.programmer,
                team_id=team_id,
            )
            db.add(p)
            programmers.append(p)
        db.flush()

        # ── Scans with realistic data ─────────────────────────────────────────
        scan_names = [
            "intellidoc_backend_v1", "auth_module_review",
            "fastapi_routes_check", "analysis_engine_v2",
            "frontend_components", "dashboard_module",
        ]

        for i, programmer in enumerate(programmers):
            # Create 2-3 scans per programmer
            num_scans = random.randint(2, 4)
            for j in range(num_scans):
                scan_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
                total_funcs = random.randint(20, 120)
                doc_funcs = random.randint(int(total_funcs * 0.4), total_funcs)

                scan = Scan(
                    name=f"{scan_names[i % len(scan_names)]}_v{j + 1}",
                    status=ScanStatus.completed,
                    created_at=scan_date,
                    completed_at=scan_date + timedelta(seconds=random.randint(2, 15)),
                    total_files=random.randint(3, 20),
                    parsed_files=random.randint(3, 20),
                    failed_files=random.randint(0, 2),
                    total_functions=total_funcs,
                    documented_functions=doc_funcs,
                    initiated_by=programmer.id,
                )
                db.add(scan)
                db.flush()

                # Deterministic score
                completeness = 40 * (doc_funcs / total_funcs)
                missing_findings = random.randint(0, 5)
                obsolete_findings = random.randint(0, 3)
                return_findings = random.randint(0, 4)
                param_penalty = missing_findings * 5 + obsolete_findings * 8
                return_penalty = return_findings * 4
                param_consistency = max(0, 40 - param_penalty)
                return_consistency = max(0, 20 - return_penalty)
                total_score = min(100, completeness + param_consistency + return_consistency)

                score = Score(
                    total_score=round(total_score, 2),
                    completeness_score=round(completeness, 2),
                    param_consistency_score=round(param_consistency, 2),
                    return_consistency_score=round(return_consistency, 2),
                    scan_id=scan.id,
                    programmer_id=programmer.id,
                )
                db.add(score)

                # Sample source file and functions
                sf = SourceFile(
                    path="app/main.py",
                    parse_status="ok",
                    function_count=total_funcs,
                    scan_id=scan.id,
                )
                db.add(sf)
                db.flush()

                # Add sample functions with findings
                sample_funcs = [
                    ("calculate_score", ["total", "documented", "findings"], True, True),
                    ("parse_docstring", ["source", "style"], True, True),
                    ("detect_drift", ["func_meta", "doc_data"], True, False),
                    ("authenticate_user", ["email", "password"], False, True),
                    ("_helper_private", ["x"], False, False),
                ]
                for fname, params, has_doc, has_ret in sample_funcs:
                    func = Function(
                        name=fname,
                        line_number=random.randint(1, 200),
                        signature=f"{fname}({', '.join(params)})",
                        docstring=f'"""Process {fname.replace("_", " ")}."""' if has_doc else None,
                        has_docstring=has_doc,
                        source_body=f"def {fname}({', '.join(params)}):\n    pass",
                        params=params,
                        has_return_statement=has_ret,
                        file_id=sf.id,
                    )
                    db.add(func)
                    db.flush()

                    if has_doc and params:
                        # Add some sample findings
                        if random.random() > 0.5:
                            df = DocumentationFinding(
                                finding_type=FindingType.missing_param_doc,
                                severity=FindingSeverity.medium,
                                explanation=f"Parameter '{params[-1]}' is not documented.",
                                extra={"param": params[-1]},
                                function_id=func.id,
                            )
                            db.add(df)

        db.commit()
        print("✅ Seed complete!")
        print("\n📋 Demo credentials:")
        print("  Project Lead : lead@intellidoc.dev / password123")
        print("  Team Lead 1  : tl1@intellidoc.dev  / password123")
        print("  Team Lead 2  : tl2@intellidoc.dev  / password123")
        print("  Programmer   : sauood@intellidoc.dev / password123")
        print("  (All other programmers: [name]@intellidoc.dev / password123)")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
