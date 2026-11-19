# IntelliDoc

A university mini project that detects drift between Python functions and their Google-style docstrings. Built from the supplied synopsis and SRS using **Next.js, React, TypeScript, FastAPI, SQLAlchemy, and PostgreSQL-compatible storage**.

The original backend under `Documents/IntelliDoc/backend` and both Word documents are untouched. The completed working copy lives in this folder.

## What works

- Signup with a required Programmer, Team Lead or Project Lead choice, followed by JWT login. The browser session uses an HttpOnly, SameSite cookie through the Next.js API proxy.
- Browser-based project creation by Project Leads and team creation by Team Leads. Unique normalized names and generated UUIDs identify each project and team.
- Programmer uploads require a matching project and team, searchable by name or ID. The backend validates the assignment and preserves it for subsequent scans of that codebase.
- Programmer, Team Lead, and Project Lead dashboards with server-enforced ownership, approved membership and team/project scope. Project Leads see both team and Programmer documentation performance across their owned projects.
- Delegated approval: Project Lead approves Team Lead project access; Team Lead approves Programmer team membership. One Programmer can have memberships across several teams and projects.
- ZIP upload, safe Python discovery, AST analysis, source snapshots, qualified function names, file parsing errors, and persistent scan history.
- Parameter drift, missing documentation, and conservative return/yield checks. Uploaded code is never imported or executed.
- Explainable 40/40/20 reliability scoring, null scores for zero functions, and function-weighted team/project rankings.
- Search/filter findings, inspect source, compare recent scores, and export JSON reports.
- Optional Groq-hosted GPT-OSS 120B for both draft generation and consistency review. Accept/edit/reject draft reviews are stored; applying a draft to the original source remains a manual step.
- Independent deterministic scanning when AI is unavailable.

## Quick start on Windows

Requirements: Python **3.12** recommended, Node.js **22 LTS** or later, npm. Commands run from this project directory unless indicated.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

For a local demo, SQLite works without an external database. Create a persistent signing key:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; from pathlib import Path; p=Path('backend/.env'); assert not p.exists(), 'Keep your existing .env'; p.write_text('JWT_SECRET_KEY='+secrets.token_urlsafe(48)+'\n')"
```

Then run:

```powershell
.\scripts\start.ps1 -Seed
```

Open **http://127.0.0.1:3000**. The launcher prints the two process IDs and a command to stop them. If a server already uses port 3000 or 8000, stop that instance before launching another.

Alternatively, use two terminals:

```powershell
# Terminal 1
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.seed
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2, from the project root
cd frontend
npm run dev
```

API reference: **http://127.0.0.1:8000/docs**.

### Demo accounts

These accounts are created only by the explicit seed command. Use them locally for evaluation.

| Role | Email | Password |
|---|---|---|
| Programmer | sauood@intellidoc.edu | ProgPass123! |
| Programmer | alice@intellidoc.edu | ProgPass123! |
| Team Lead | teamlead@intellidoc.edu | TeamPass123! |
| Project Lead | projectlead@intellidoc.edu | LeadPass123! |

Seeding an already populated database does not reset or overwrite users. The seed includes an actual scan of `samples/student_api/students.py`, with deliberately outdated documentation. Scores are computed by the analysis engine, not fabricated dashboard values.

Create a sample upload:

```powershell
Compress-Archive -Path samples/student_api/* -DestinationPath samples/student-api.zip -Force
```

### Demo walkthrough

1. Sign in as the programmer and inspect the seeded codebase.
2. Open `calculate_grade`: the `maximum` parameter is absent from its docstring.
3. Open `enroll_student`: `semester` is missing and the old `batch` parameter is obsolete.
4. Open `active_students`: its entire docstring is missing.
5. Choose New scan, select the existing project and team, upload the sample ZIP, inspect Files and Score breakdown, and export the report.
6. Fix documentation in your own copy, ZIP it again, and rescan the same codebase.
7. Sign in as each lead to see the scoped rankings.
8. If AI keys are configured, explicitly request assistance on a selected function. Otherwise the API reports a clear configuration failure and preserves the scan.

## PostgreSQL and containers

For PostgreSQL, set `DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/intellidoc` in `backend/.env`. URL-encode special characters in database credentials. Run `python -m alembic upgrade head` in the backend directory before starting production.

A full container stack is included. Put strong, URL-safe values for `POSTGRES_PASSWORD` and `JWT_SECRET_KEY` in a root `.env` file, then:

```powershell
docker compose up --build -d
docker compose exec backend python -m app.seed
```

The backend and database are internal to the container network; the frontend is available on port 3000. The database has a persistent named volume. The container seed creates demo accounts, but sample scans are not seeded because the sample directory is outside the backend image; upload the sample ZIP.

Before hosting over HTTPS, set `COOKIE_SECURE=true` and `APP_ORIGIN` to the frontend origin. Do not use demo accounts for a public deployment. Production refuses to start without an explicit signing key of at least 32 characters.

The initial migration targets a **fresh database**. Do not point this version at the older backend's existing database: the schema adds source snapshots, file errors, and AI reviews. Back up and migrate old data explicitly if you need it.

## Optional AI configuration

Set keys on the backend only, never in browser code:

```dotenv
GROQ_API_KEY=your-key
GROQ_MODEL=openai/gpt-oss-120b
```

Restart the API after changes. Both AI tasks use one Groq-hosted model. Create a key at https://console.groq.com/keys and store it as GROQ_API_KEY on the backend. Keep your account on the Free plan for a demo within its allowance. As checked on 18 November 2026, Groq lists GPT-OSS 120B at 30 requests/minute, 1,000/day, 8,000 tokens/minute and 200,000/day on Free. Limits are shared across the organization. Check your exact allowance at https://console.groq.com/settings/limits. Paid Developer token prices apply after a plan upgrade. See https://console.groq.com/docs/rate-limits and https://console.groq.com/docs/billing-faqs. The previously configured Llama model has lost free/developer access. The application does not enable billing or retry paid requests. It sends only the selected stored function, never a whole archive. Functions exceeding the context limit are rejected without sending partial code.

Provider reference: [Groq chat API](https://console.groq.com/docs/api-reference). Frontend reference: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation).

## Free cloud deployment

The deployment target is two Render Free Web Services plus Neon Free PostgreSQL. The complete visual setup guide is `final_submission/IntelliDoc_Deployment_and_Flow_Guide.pdf`. Deployment and live provider calls still need verification.

| Setting | Backend service | Frontend service |
|---|---|---|
| Root directory | `backend` | `frontend` |
| Native runtime | Python 3 | Node |
| Build command | `pip install -r requirements.txt` | `npm ci && npm run build` |
| Start command | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` | `npm start -- --hostname 0.0.0.0 --port $PORT` |
| Version | `PYTHON_VERSION=3.12.12` | `NODE_VERSION=22` |

On the backend, set `ENVIRONMENT=production`, a generated persistent `JWT_SECRET_KEY` of at least 32 characters, the Neon direct TLS connection URL as `DATABASE_URL`, `GROQ_API_KEY`, and `GROQ_MODEL=openai/gpt-oss-120b`. If your existing environment explicitly selects Llama, replace that model value. Keep all credentials in the backend environment.

On the frontend, set `NODE_ENV=production`, `BACKEND_URL` to the actual backend HTTPS origin without `/api/v1` or a trailing slash, `APP_ORIGIN` to the actual frontend HTTPS origin, and `COOKIE_SECURE=true`. Leave `NEXT_DIST_DIR` unset so build and start both use `.production`.

Create a fresh Neon database and let backend startup run the migration. Render Free storage is ephemeral, so PostgreSQL holds the persistent users, source snapshots and scan results. Existing local SQLite records require an explicit data migration if needed. Users create their accounts and set up projects and teams through the deployed web app as described below.

Render Free services sleep after 15 idle minutes and share 750 active instance-hours per workspace each month. Two services consume that allowance together. Neon Free currently includes 100 CU-hours and 1 GB storage per project. Monitor hosting, database, bandwidth/build and AI allowances. Source links are https://render.com/docs/free and https://neon.com/pricing. Vercel Functions' 4.5 MB payload cap conflicts with the current 10 MB upload policy, so this setup uses a Render Node service for the Next.js proxy.

## Project and team setup

1. **Project Lead:** choose this role during signup. Open Projects, enter a unique project name and select Create project. Copy its generated project ID and share it with the Team Lead.
2. **Team Lead:** choose this role during signup. In Project access, find the existing project by name or its complete ID and request access. The owning Project Lead approves it in Projects. You can then create teams in that approved project through Teams and share their generated IDs.
3. **Programmer:** choose this role during signup. In Memberships, find/select the project and one of its teams, then request access. The responsible Team Lead approves or rejects it in Teams. Repeat for any additional teams/projects. Once approved, open Scans → New scan, name the codebase, select an approved project/team, choose a Python ZIP and run the scan.
4. **Review:** Team Leads see their team members and submissions. Project Leads see all team and Programmer documentation performance plus underlying scans in their owned projects. Their selectors support multiple teams/projects. Programmers can read and modify only their own submissions. Project Leads do not approve individual Programmer memberships.

The API rejects missing or unknown IDs, a team from another project, duplicate project/team names, unapproved team creation/uploads, unrelated approvers and actions forbidden for the signed-in role. Pending and Rejected users can log in but cannot perform the gated operation. Rejected requests may be resubmitted; duplicate active requests reuse the existing record. Names are normalized for spacing, Unicode and case before checking uniqueness. UUIDs are generated by the server. A codebase keeps its assignment on rescans; submit a new codebase for a different project/team.

Authenticated users can search project/team names and IDs to request permission. This metadata directory exposes no unrelated source or results. Upload selectors show only approved memberships. Signup selects an account role and creates no organization records. A Project Lead may create their own project; a Team Lead requires that project's lead approval before creating teams. Approvals are scoped relationships rather than global role elevation.

Existing databases upgrade through `alembic upgrade head` (revision `0003`); the Windows launcher runs this automatically. Back up your database before upgrading. Unambiguous legacy links are backfilled; existing valid relationships receive explicitly labelled migration grants. Ambiguous legacy assignments remain readable through compatibility rules. All new access uses delegated approval in the browser. `app.manage` is a privileged database maintenance tool, not the normal onboarding flow.

## Scoring policy

The implementation resolves the SRS's proposed scoring rules as follows:

- Completeness: `40 × documented / total`.
- Parameter consistency: `max(0, 40 − parameter penalties) × documented / total`.
- Return consistency: `max(0, 20 − return/yield penalties) × documented / total`.
- Penalties: high 4, medium 2, low 1. Missing documentation is not penalized a second time.
- No functions: null score, displayed as N/A.
- AI never affects scores. The first-release code-quality field mirrors the DRS.
- Lead rankings: function-weighted scores from each programmer's latest scan per codebase. Project aggregation includes only that project's codebases.

These weights are a proposed academic policy, not a validated measure of overall programming ability.

## Validation

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ../frontend
npm run typecheck
npm run build
npm start
```

See `TESTING.md` for the verified checks and remaining environment-dependent checks.

## Limits and deployment notes

- Google-style docstrings and Python only; no type inference, runtime correctness proof, or automatic source editing.
- Uploads: 10 MB compressed, 30 MB expanded, 1 MB per Python file, 1,000 archive entries. ZIP traversal, symlinks, encrypted entries, and duplicates are rejected.
- Scans run in a worker thread within the request and persist results. This is suitable for the mini-project's moderate codebases, not a distributed job queue.
- Basic login/registration/AI rate limiting is per API process. A production deployment with multiple workers needs a shared rate limiter and reverse-proxy request limits.
- Lead selectors support multiple owned projects/teams. Directory search supports name or complete UUID lookup; each results page and owned organization list is limited to 100 records in this mini-project UI.
- Approval records retain the current state and latest decision. Revocation, immutable decision history, lead transfer and archived-project controls remain future extensions.
- Scans are paginated 50 at a time; codebase listing shows up to 100.
- The dashboard chart displays recent scan scores across codebases; inspect a codebase's own scans for a like-for-like comparison.
- Local sessions without a configured signing key expire when the backend restarts. Set the persistent key as described above.
- Local preview is not a public deployment. PostgreSQL/container startup and actual AI-provider calls need separate verification in the target environment.

