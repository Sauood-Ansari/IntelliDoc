"""Explicit project/team assignments with unique organization names.

Keep existing submissions and infer legacy assignments only when unambiguous.
The column checks also support fresh installs whose 0001 uses current metadata.
"""
import unicodedata

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    sqlite = bind.dialect.name == "sqlite"
    if sqlite:
        with op.get_context().autocommit_block():
            bind.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        for table, display in (("projects", "project_name"), ("teams", "team_name")):
            columns = {column["name"] for column in sa.inspect(bind).get_columns(table)}
            if "name_key" not in columns:
                op.add_column(table, sa.Column("name_key", sa.String(300), nullable=True))
                rows = bind.execute(sa.text(f"SELECT {table[:-1]}_id AS id, {display} AS name FROM {table}"))
                used = set()
                for row in rows.mappings().all():
                    name = " ".join(unicodedata.normalize("NFKC", row["name"]).split())
                    if not name:
                        name = "Legacy " + table[:-1]
                    key = name.casefold()
                    if key in used:
                        name = name[:50] + " (" + str(row["id"]) + ")"
                        key = name.casefold()
                    used.add(key)
                    bind.execute(sa.text(f"UPDATE {table} SET {display}=:name, name_key=:key WHERE {table[:-1]}_id=:id"),
                                 {"name": name, "key": key, "id": row["id"]})
                with op.batch_alter_table(table) as batch:
                    batch.alter_column("name_key", existing_type=sa.String(300), nullable=False)
                    batch.create_unique_constraint(f"uq_{table}_name_key", ["name_key"])

        team_columns = {column["name"] for column in sa.inspect(bind).get_columns("teams")}
        lead_unique = next((constraint for constraint in sa.inspect(bind).get_unique_constraints("teams")
                            if constraint["column_names"] == ["team_lead_id"]), None)
        if "project_id" not in team_columns or lead_unique:
            with op.batch_alter_table("teams", naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"}) as batch:
                if lead_unique:
                    batch.drop_constraint(lead_unique["name"] or "uq_teams_team_lead_id", type_="unique")
                if "project_id" not in team_columns:
                    batch.add_column(sa.Column("project_id", sa.Uuid(), nullable=True))
                    batch.create_foreign_key("fk_teams_project_id", "projects", ["project_id"], ["project_id"])
        codebase_columns = {column["name"] for column in sa.inspect(bind).get_columns("codebases")}
        if "team_id" not in codebase_columns:
            with op.batch_alter_table("codebases") as batch:
                batch.add_column(sa.Column("team_id", sa.Uuid(), nullable=True))
                batch.create_foreign_key("fk_codebases_team_id", "teams", ["team_id"], ["team_id"])

        teams = bind.execute(sa.text("SELECT team_id FROM teams WHERE project_id IS NULL")).scalars().all()
        for team_id in teams:
            projects = bind.execute(sa.text("""
                SELECT DISTINCT c.project_id FROM codebases c JOIN users u ON u.user_id=c.owner_id
                WHERE u.team_id=:team AND c.project_id IS NOT NULL
            """), {"team": team_id}).scalars().all()
            if len(projects) == 1:
                bind.execute(sa.text("UPDATE teams SET project_id=:project WHERE team_id=:team"),
                             {"project": projects[0], "team": team_id})
        bind.execute(sa.text("""
            UPDATE codebases SET team_id=(
                SELECT t.team_id FROM teams t JOIN users u ON u.team_id=t.team_id
                WHERE u.user_id=codebases.owner_id AND t.project_id=codebases.project_id
            ) WHERE team_id IS NULL
        """))
    finally:
        if sqlite:
            with op.get_context().autocommit_block():
                bind.exec_driver_sql("PRAGMA foreign_keys=ON")


def downgrade():
    raise RuntimeError("Restore a pre-migration backup to undo explicit organization assignments safely")
