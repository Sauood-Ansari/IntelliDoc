# Synopsis

| Synopsis Of     “AI-Assisted Documentation Drift Detector with Team                   Code-Quality Oversight ”    Submitted By Name: Sauood Ansari Faculty No: 25CAMSA151 Enrollment No: GN4457 Course: MCA Semester: III  Under Supervision of Prof. Aasim Zafar Mr. Kausar Ali Mr. Mohd Adnan  Department of Computer Science Aligarh Muslim University Aligarh |
| --- |

**1. Project Title**

IntelliDoc: An AI-Assisted Documentation Drift Detector with Team Code-Quality Oversight

## 2. Problem Identification / Problem Statement

As code evolves, its documentation quietly stops matching it. A parameter is added, a return value changes, but the docstring is never updated. This is documentation drift, and unlike missing documentation, it is more dangerous because it looks trustworthy while being wrong. Team leads and project leads have no automated way to see which functions' documentation has drifted from the code, or to compare documentation reliability and code quality across programmers, without manually reading through every file, a process that does not scale as team or codebase size grows.

## 3. Motivation / Need

**Who faces the problem: **Programmers whose documentation silently goes stale as their code changes; team leads who review their programmers' work; project leads who oversee multiple teams without reviewing every line themselves.

**Why the existing method is inadequate: **Manual review cannot reliably catch drift, is slow and inconsistent, and does not scale. Existing documentation tools only check whether a comment exists, not whether it still matches the code, and none give leads an objective, comparable measure across programmers.

**Expected improvement: **A system that detects drift between a function's documentation and its actual implementation, flags functions with missing documentation and offers an AI-generated draft as a side feature, and turns overall documentation reliability into an objective, rankable score for team leads and project leads.

**Who benefits: **Programmers get early warning when their documentation has drifted, plus an assisted starting point when documentation is missing; team leads and project leads get objective visibility into documentation reliability and code quality without reading every file.

## 4. Objectives

To build a static-analysis engine (Python's ast module) that detects drift between a function's docstring and its actual signature/behaviour.

As a side feature, to use AI to generate a draft docstring for functions with no documentation at all, for the programmer to review and accept or edit.

To provide an optional, on-demand AI-based check that flags likely logical mismatches between a function's documentation and its implementation, for cases the deterministic check cannot confidently resolve.

To implement a three-tier role-based system (Programmer, Team Lead, Project Lead) where each higher role views ranked quality metrics for the tier below it.

To compute an explainable documentation-reliability and code-quality score per programmer, aggregable per team, with a dashboard for each role.

## 5. Proposed Solution

IntelliDoc is a web application with a Next.js/TypeScript frontend and a Python/FastAPI backend, using PostgreSQL for storage. A Programmer scans a Python codebase; the system parses it with Python's ast module and compares each function's docstring against its actual parameters and return behaviour, flagging drift where they disagree. Where a function has no documentation at all, AI generates a draft docstring as a side feature, for the programmer to accept or edit. On request, the Programmer can also trigger an AI-based logical-consistency check on a specific function for a deeper opinion. Results roll up into a per-programmer documentation-reliability score; Team Leads see a ranked view of their Programmers, and Project Leads see the same view one level up, across teams.

**System Architecture**

![Embedded image or diagram](assets/Synopsis_image_01.png)

*Fig. 1: **IntelliDoc** system architecture, showing the flow from the frontend through the backend, the drift-detection/scoring/AI layers, the database, and the three-tier role hierarchy.*

## 6. Preliminary Functional Requirements

The system shall:

FR1 – Support role-based login (Programmer, Team Lead, Project Lead).

FR2 – Allow a Programmer to scan a Python codebase.

FR3 – Detect drift between a function's docstring and its actual signature (parameters/return value) via AST-based comparison.

FR4 – Flag functions with no documentation, and, as a side feature, generate a draft docstring using AI, subject to Programmer approval.

FR5 – Allow a Programmer to optionally trigger an AI-based logical-consistency check on a chosen function.

FR6 – Compute a documentation-reliability and quality score per Programmer per scan, with history.

FR7 – Let a Team Lead view a ranked list of their Programmers by score.

FR8 – Let a Project Lead view a ranked list of Team Leads/teams by aggregated score.

## 7. Preliminary Non-Functional Requirements

NFR1 (Security): Role-based access; a Programmer cannot view another Programmer's scan detail unless authorized.

NFR2 (Usability): Dashboards understandable without tool-specific training.

NFR3 (Performance): A moderate-sized codebase (~5,000–10,000 lines) scans quickly via deterministic checks; AI is used only for generation and on-demand checks, not on every function.

NFR4 (Reliability): Deterministic checks work even if AI is temporarily unavailable.

NFR5 (Maintainability): AI integration sits behind a common interface so the underlying service can change without affecting the core pipeline.

## 8. Scope

**Included:**

Documentation-drift detection for Python (docstring vs. actual signature, Google-style docstrings).

AI-generated draft documentation for missing docstrings (side feature).

An optional, per-function, AI-based logical-consistency check, triggered by the Programmer.

Three-tier role-based dashboards with scan history and score trends.

**Not included:**

Automatic, always-on logical-error scanning across an entire codebase (the deeper AI check is opt-in, per function).

General-purpose bug detection beyond documentation-vs-implementation consistency.

Languages other than Python in the first release.

Git-history-based drift timing (the system compares current documentation against current code, not when drift began); CI/CD integration (future work).

Any paid AI usage; free-tier services only.

## 9. Feasibility Study

**Technical: **AST parsing, comparison logic, scoring, and RBAC dashboards use tools already familiar or in active use. AI is used only where it adds value (generation and an on-demand check), keeping usage light and free-tier-friendly.

**Operational: **The three roles map to real organisational roles, so users need no special training to understand the dashboards.

**Economic: **Zero recurring cost. Free-tier hosting and free-tier AI access throughout, matching student budget constraints.

## 10. Proposed Technology Stack

| Component | Proposed Technology |
| --- | --- |
| Front-end | Next.js, React, TypeScript |
| Back-end | Python, FastAPI |
| Code Parsing | Python ast module (Google-style docstrings) |
| Database | PostgreSQL |
| AI (Documentation Generation) | Groq (Llama 3.3 70B), free tier |
| AI (Logical Consistency Check) | Google Gemini (Flash), free tier |
| Authentication | JWT-based, role field (Programmer / Team Lead / Project Lead) |
| Version Control | Git / GitHub |
| Deployment | Vercel (frontend) + Render/Railway free tier (backend + DB) |

## 11. Preliminary Development Plan

| Phase | Activity |
| --- | --- |
| 1 | Problem identification and synopsis |
| 2 | Requirements analysis and SRS |
| 3 | System design (architecture, RBAC, AI-interface design) |
| 4 | Database design |
| 5 | Implementation: parser, deterministic checks, scoring |
| 6 | Implementation: AI integration (generation and consistency check) |
| 7 | Implementation: role-based dashboards |
| 8 | Testing and evaluation |
| 9 | Documentation and final report |

## 12. Expected Outcome

A working application where a Programmer scans a Python codebase and sees which functions' documentation has drifted from the actual code, receives an AI-generated draft for functions with no documentation at all, and can optionally request a deeper AI-based consistency check on any function. A Team Lead sees a ranked, objective view of their Programmers' documentation reliability and code quality, and a Project Lead sees the same view one level up, across teams. This reduces manual review effort while keeping the core drift-detection mechanism deterministic and explainable, with AI used only as a side feature and an on-demand deeper check.

## 13. References

[1] Python ast module documentation. Available: https://docs.python.org/3/library/ast.html

[2] Google-style Python docstring convention. Available: https://google.github.io/styleguide/pyguide.html

[3] Groq documentation. Available: https://console.groq.com/docs

[4] Google Gemini documentation (free tier). Available: https://ai.google.dev/

[5] FastAPI documentation. Available: https://fastapi.tiangolo.com/

*End of Document*
