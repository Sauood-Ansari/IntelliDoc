# Validation record

The implementation is based on both supplied Word documents. Existing source was copied into this workspace; no original databases or documents were modified.

## Verified

- Delegated approval baseline on 19 November 2026: all 64 backend tests passed (273 dependency deprecation warnings, 36.22 seconds), and the Next.js production build including TypeScript checking passed. Coverage includes pending-write denial, the responsible Project Lead approving Team Lead access, the responsible Team Lead approving Programmer memberships, rejection/retry, unrelated approvers, multiple memberships, project-wide Programmer rankings and isolated migrations. A complete local Chrome browser check passed role signup → project → pending project request → Project Lead approval → team → pending team membership → Team Lead approval → assigned upload → export → both lead dashboards, including mobile overflow checks and no browser errors. The sample produced 8 functions and DRS 69.75. Local revision 0003 preserves existing submission data and records legacy migration grants separately. Test clients now avoid creating tables in the user's local database. Live-provider and cloud checks below remain unverified.

- Role and organization update on 18 November 2026: 60 backend tests passed (132 dependency deprecation warnings), TypeScript checking passed and the Next.js production build passed. Coverage includes signup for all three roles, project/team creation permissions, canonical name uniqueness, required and matching upload assignments, immutable rescan assignments, resource isolation, multiple lead scopes, and fresh/legacy Alembic revision 0002 migrations. A local Chromium browser check completed signup → project → team → assigned ZIP scan → JSON export → both lead dashboards, with 8 extracted functions, DRS 69.75 and no browser errors. Desktop and 390-pixel mobile layouts were inspected. The workspace SQLite database was backed up and upgraded to revision 0002, preserving all table record counts and passing foreign-key checks. Live cloud deployment and AI-provider calls were not part of this check.

- Deployment model update on 18 November 2026: both AI tasks now select Groq-hosted `openai/gpt-oss-120b`. The shared-adapter tests explicitly check that model ID. All 50 backend tests passed (108 deprecation warnings, 20.28 seconds), and the production build including TypeScript checking passed. The deployment guide, 20-page report and 15-slide presentation use the same model. Live provider calls and cloud deployment remain unverified.

- Final submission audit on 13 November 2026: backend suite passed again (50 tests, 108 warnings, 17.90 seconds). A fresh Next.js production build, including TypeScript checking and static page generation, passed using `.audit-production-20261113` as its output directory. The main progress report matches the verified 20-page concise copy; the 15-slide presentation matches its audited validation hash. Live integration and performance limitations below remain applicable.

- Documentation alignment recheck on 13 November 2026: all 50 backend tests passed again (108 deprecation warnings), and TypeScript `tsc --noEmit` passed. The audited submission files are in `final_submission/`. Live-provider, deployment and performance limitations below still apply.

- Earlier 50-test coverage included end-to-end ZIP scans, partial parse failures, unsafe paths, invalid archives, upload/expansion/entry limits, empty scans, cross-role access isolation, source persistence, stored AI review, and AI-independent scores. The shared hosted-model adapter checks cover context and credential validation, timeout handling, and the 75.2 scoring example. Current coverage is the 60-test suite above; signup now intentionally accepts all three user-selected roles.
- Parser regression checks cover nested return scope, positional-only and keyword-only parameters, async functions, static methods, method receivers, generators, explicit None returns, and docstring section boundaries.
- TypeScript checking passed again after the single-Llama update. A complete Next.js production build passed in the earlier validation run.
- In-browser programmer login, dashboard display, scan navigation, function source, findings, and the score chart were inspected.
- SQLite-backed local API and frontend work together through the Next.js session proxy.
- Production HTTP checks verified login, HttpOnly/SameSite cookie settings, profile and scan retrieval, cross-origin request rejection, and logout.
- Alembic initial migration reached revision 0001 on a fresh SQLite database; PostgreSQL schema DDL compiled successfully.
- Extra aggregation tests verified project isolation, latest-scan replacement, and authorized lead access.

## Not live-verified

- Groq-hosted GPT-OSS requests: the current model has been tested with controlled responses, not a live provider request. Live model availability and output quality still require verification with the deployment account. During the earlier Llama validation, automatic approval review blocked clicking the browser AI action because it could transmit source externally. That historical browser rejection was not bypassed.
- PostgreSQL and Docker runtime: configuration and schema support are supplied, but a PostgreSQL server/container runtime was not available for this verification.
- No public hosting deployment was performed.

## Notes

The first production build compiled but hit a Windows file-access error in its output directory. Building into a dedicated fresh production output directory completed successfully.

Dependency deprecation warnings do not fail the tests. The score policy remains the proposed academic policy described in the SRS and README.

