# IntelliDoc

A university mini project that detects drift between Python functions and their Google-style docstrings. Built from the supplied synopsis and SRS using **Next.js, React, TypeScript, FastAPI, SQLAlchemy, and PostgreSQL-compatible storage**.

The original backend under `Documents/IntelliDoc/backend` and both Word documents are untouched. The completed working copy lives in this folder.

## What works

- Programmer registration and JWT login; the browser session uses an HttpOnly, SameSite cookie through the Next.js API proxy.
- Programmer, Team Lead, and Project Lead dashboards with server-enforced ownership and team/project scope.
- ZIP upload, safe Python discovery, AST analysis, source snapshots, qualified function names, file parsing errors, and persistent scan history.
- Parameter drift, missing documentation, and conservative return/yield checks. Uploaded code is never imported or executed.
- Explainable 40/40/20 reliability scoring, null scores for zero functions, and function-weighted team/project rankings.
- Search/filter findings, inspect source, compare recent scores, and export JSON reports.
- Optional Groq draft generation and Gemini consistency review. Accept/edit/reject draft reviews are stored; applying a draft to the original source remains a manual step.
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
5. Upload the sample ZIP, inspect Files and Score breakdown, and export the report.
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
GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash
```

Restart the API after changes. Obtain and configure your own free-tier accounts; available models, quotas, and pricing are controlled by each provider. The application does not enable billing or retry paid requests. It sends only the selected stored function, never a whole archive. Functions exceeding the context limit are rejected without sending partial code.

Provider references: [Groq chat API](https://console.groq.com/docs/api-reference) and [Gemini content generation](https://ai.google.dev/api/generate-content). Frontend reference: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation).

## Account and organization administration

Public registration creates only unassigned Programmers. Roles, teams, and initial project assignments are managed by a trusted local CLI, preventing users from granting themselves access.

Run in `backend` using the virtual environment Python:

```powershell
python -m app.manage list
python -m app.manage add-user --name "Team Lead" --email lead@example.com --role "Team Lead"
python -m app.manage add-team --name "Team Beta" --lead-email lead@example.com
python -m app.manage assign-user --email developer@example.com --team TEAM_UUID
python -m app.manage add-user --name "Project Lead" --email project@example.com --role "Project Lead"
python -m app.manage add-project --name "University Project" --lead-email project@example.com
python -m app.manage assign-codebase --codebase CODEBASE_UUID --project PROJECT_UUID
```

Passwords are prompted securely rather than placed in shell command history. A Programmer may register additional codebases in a project only after the administrator has assigned an existing codebase to that project.

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
- The lead overview currently selects the first project assigned to that lead; use one project per Project Lead in this version.
- Scans are paginated 50 at a time; codebase listing shows up to 100.
- The dashboard chart displays recent scan scores across codebases; inspect a codebase's own scans for a like-for-like comparison.
- Local sessions without a configured signing key expire when the backend restarts. Set the persistent key as described above.
- Local preview is not a public deployment. PostgreSQL/container startup and actual AI-provider calls need separate verification in the target environment.

