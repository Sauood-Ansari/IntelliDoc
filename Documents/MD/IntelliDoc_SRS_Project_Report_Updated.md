# IntelliDoc SRS Project Report Updated

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_10.png)

## **INDEX**

**Content****	Page No.**

**Chapter 1: INTRODUCTION	1**

1.1 Introduction	1

1.2 Literature Survey	1

1.3 Present State of the Art and Shortcomings	2

1.4 Realization of the Problems	2

1.5 Introduction of the Proposed Work	2

1.6 Broad Outline of the Work	3

**Chapter 2: PROBLEM FORMULATION	4**

2.1 Problem Definition and Detailed Description	4

2.2 Various Aspects of the Problem	4

2.3 Critical View of Present Approaches	5

2.4 Scientific Novelty and Need of the Work	5

2.5 Proposed System / Method of Solution	5

**Chapter 3: SYSTEM ANALYSIS AND DESIGN	7**

3.1 Requirement Specification	7

3.2 Information Collection / Requirements Elicitation	9

3.3 Analysis and Development of the Actual Solution	9

3.4 Description of Various Modules	10

3.5 System Development Tools	11

3.6 Choice of Language	11

3.7 Choice of System for Implementation	12

3.8 System Architecture	12

3.9 Detailed Design Diagrams	13

3.10 Key Algorithms	17

3.11 Use Case Specifications	18

3.12 Database Design and Data Dictionary	19

3.13 Technology Stack Justification	20

3.14 Design Tools and Limitations	20

**Chapter 4: SYSTEM IMPLEMENTATION	22**

4.1 Hardware Requirements	22

4.2 Software Requirements	22

4.3 Input Requirements	22

4.4 Operation Manual	23

4.5 Output Reports / Results	24

4.6 Implementation Status	24

**Chapter 5: RESULT AND DISCUSSION	25**

5.1 Evaluation Framework and Interpretation of Results	25

5.2 Application Areas and Scope of Work	25

5.3 Discussion	25

**Chapter 6: CONCLUSION	27**

6.1 Advantages and Special Features	27

6.2 Limitations	27

6.3 Future Extensions	27

References	30

Appendix A: Configuration Parameters	32

Appendix B: Draft API Specification	33

Appendix C: Scoring Rules	34

Appendix D: Example Analysis Results	35

## **LIST OF ABBREVIATIONS**

| Abbreviation | Meaning |
| --- | --- |
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| AST | Abstract Syntax Tree |
| DFD | Data Flow Diagram |
| ER | Entity Relationship |
| FR | Functional Requirement |
| JWT | JSON Web Token |
| NFR | Non-Functional Requirement |
| RBAC | Role-Based Access Control |
| SRS | Software Requirements Specification |
| UI | User Interface |
| URL | Uniform Resource Locator |

## **CHAPTER 1: INTRODUCTION**

### **1.1 Introduction**

Modern software systems are changed continuously. New functions are added, existing parameters are renamed, return behaviour is revised, and internal implementations evolve as requirements change. Documentation is expected to help developers understand the system, but it is itself another artifact that must be maintained. When code changes without a corresponding update to its documentation, the documentation can gradually diverge from the implementation. This condition is particularly problematic when the documentation remains syntactically complete and appears authoritative to a reader.

Software documentation is used during development, maintenance, and program comprehension. Empirical work has shown that practitioners do not always update documentation as promptly or completely as recommended, while other studies have demonstrated that outdated documentation can still be consulted in practice. [1][2] These observations motivate tools that reduce the cost of maintaining reliable documentation rather than assuming that manual discipline alone will keep it synchronized.

IntelliDoc is proposed to address a focused part of this problem: function-level documentation drift in Python code. It uses Python's AST infrastructure to inspect source-level structure and performs deterministic comparisons between function signatures and their docstrings. The system then provides explainable findings, stores scan history, computes documentation-related quality metrics, and exposes the information through dashboards appropriate to the user's organizational role.

### **1.2 Literature Survey**

The following review is organized chronologically, as expected in the project-report structure. The purpose is not to claim that IntelliDoc is the first system in this area, but to place the proposed work in the context of documented research on software documentation quality, maintenance, consistency, and automated generation.

**Table 1.1: Summary of Related Literature**

| Year | Work | Main contribution / finding | Relevance to IntelliDoc |
| --- | --- | --- | --- |
| 2003 | Lethbridge, Singer & Forward : How software engineers use documentation: the state of the practice | Empirical studies examined how engineers use and update documentation and reported that documentation is not always updated as timely or completely as recommended. [1] | Establishes the maintenance problem and motivates automated assistance. |
| 2006 | de Souza, Anquetil & de Oliveira : Which Documentation for Software Maintenance? | Surveyed software maintainers to understand which documentation artifacts are useful during maintenance. [2] | Supports the view that documentation quality and usefulness matter during maintenance. |
| 2013 | Khamis, Rilling & Witte : JavadocMiner | Proposed heuristics for assessing qualities of inline documentation, including consistency between source code and comments. [3] | Demonstrates that source/documentation consistency can be assessed automatically. |
| 2014 | Kuhn & Bergel : Verifiable Source Code Documentation in Controlled Natural Language | Presented a method for checking documentation consistency and accuracy using controlled natural language, a reasoner, and a query engine. [4] | Shows the value of automated consistency verification while also illustrating that richer semantic analysis can be complex. |
| 2020 | Arthur : Automatic Source Code Documentation using Code Summarization Technique of NLP | Explored automated source-code documentation generation using code summarization and natural-language generation. [5] | Relates to IntelliDoc's optional AI-assisted documentation generation. |
| 2024 | Tan, Wagner & Treude : Detecting outdated code element references in software repository documentation | Proposed automated detection of outdated code-element references and studied repositories at scale. [6] | Demonstrates the continuing need for automated detection of code-documentation mismatches. |
| 2026 | Kiecker et al. : CASCADE: Detecting Inconsistencies between Code and Documentation with Automatic Test Generation | Investigated LLM-assisted consistency detection using generated tests and cross-checking of code/documentation relationships. [7] | Represents recent work toward deeper semantic consistency analysis and supports the idea of keeping AI-assisted checks separate from deterministic checks. |

### **1.3 Present State of the Art and Its Shortcomings**

Current software ecosystems provide several ways to produce or validate documentation. Language-specific documentation generators can construct reference pages from docstrings or comments, static-analysis tools can identify certain structural properties, and modern AI models can generate natural-language descriptions from source code. However, these approaches solve different parts of the problem. Presence checking answers whether documentation exists; generation creates text; deeper semantic techniques attempt to assess whether a description is accurate. The specific requirement addressed by IntelliDoc is the focused, repeatable comparison between documentation and structural facts that can be extracted deterministically from the current Python source.

Research on outdated documentation shows that synchronizing source code and documentation remains difficult, especially when software evolves. [6] More advanced approaches can improve semantic coverage but generally require additional reasoning, execution, or model-based analysis. IntelliDoc therefore takes a deliberately layered position: use deterministic rules where the evidence is explicit, then permit an on-demand AI check when a programmer wants a deeper opinion. This reduces unnecessary AI usage and preserves explainability.

### **1.4 Realization of the Problems**

The problem becomes visible when a function is modified without a corresponding update to its docstring. For example, a function that originally accepts two parameters may later gain a third parameter. If the documentation is not updated, a developer reading the docstring may not realize that the function now requires or accepts additional information. Similar issues arise when names change, when obsolete parameter descriptions remain, or when return-related documentation no longer matches information that can be inferred from the implementation.

At an individual-developer level, these issues create maintenance overhead and increase the chance of incorrect assumptions. At a team level, leads may have to inspect many files to understand documentation health. At project level, manual inspection does not scale. The need is therefore not merely to generate more documentation, but to provide visibility into whether existing documentation continues to correspond to the code.

### **1.5 Introduction of the Proposed Work**

IntelliDoc provides a web-based workflow in which a Programmer initiates analysis of a Python codebase. The backend processes the source using Python AST, extracts functions and documentation information, applies deterministic comparison rules, and stores the resulting findings and metrics. A separate AI layer is available for two optional tasks: generating draft documentation for functions that have no docstring and performing a deeper logical-consistency check when explicitly requested.

The system also supports three role levels. The Programmer receives function- and scan-level feedback. The Team Lead receives an authorized view of programmers and their metrics. The Project Lead receives higher-level aggregated information across teams. This structure is intended to turn individual scan results into an understandable quality-oversight view without requiring manual reading of every source file.

### **1.6 Broad Outline of the Work**

Chapter 1 introduces the problem and reviews related work. Chapter 2 formulates the problem in greater detail and describes the proposed method. Chapter 3 contains the detailed requirements, system analysis, architecture, modules, algorithms, database model, use cases, and design diagrams. Chapter 4 describes implementation-oriented requirements, interfaces, operating procedures, and system outputs. Chapter 5 defines the evaluation framework and discusses the expected interpretation of results without fabricating measurements. Chapter 6 concludes the work, summarizes its advantages, records limitations, and identifies future extensions.

## **CHAPTER 2: PROBLEM FORMULATION**

### **2.1 Problem Definition and Detailed Description**

The central problem addressed by IntelliDoc is the detection of documentation drift between a Python function and its associated docstring. Documentation drift is defined here as a condition in which information represented by the documentation no longer corresponds to source-level facts that can be reliably extracted from the current implementation. The project focuses on function-level documentation, especially the relationship between function signatures, parameters, return-related information, and Google-style docstrings.

Two related conditions must be distinguished. First, a function may have no documentation at all. This is a completeness problem. Second, a function may have documentation that exists but is stale or inconsistent with the implementation. This is a drift problem. The second condition is especially important because the presence of a docstring can create an expectation of reliability. IntelliDoc therefore reports missing documentation separately from deterministic mismatches wherever practical.

### **2.2 Various Aspects of the Problem**

#### **Technical aspect**

A codebase contains a large number of functions and source files. Manual comparison of signatures and docstrings is repetitive, while arbitrary runtime semantics cannot be inferred perfectly from syntax alone.

#### **Documentation aspect**

Documentation is written in natural language and may contain parameter, return, and descriptive information. Its structure must therefore be interpreted sufficiently to compare with source-level facts.

#### **Developer workflow**

Developers need immediate, understandable feedback about which functions require attention rather than a general quality number with no explanation.

#### **Team oversight**

Team Leads need aggregated visibility over multiple programmers without manually reading every file.

#### **Project oversight**

Project Leads need higher-level metrics to observe trends and compare authorized groups, while the project remains careful not to equate a documentation metric with total programming ability.

#### **Scalability**

The system should handle moderate-sized codebases efficiently through deterministic checks and reserve AI calls for situations in which they add value.

### **2.3 Critical View of Present Approaches**

Manual review remains useful because developers can interpret context and intent, but it is slow and dependent on consistent reviewer effort. Traditional documentation tools often emphasize the creation or rendering of documentation rather than a direct comparison with the current function structure. Heuristic approaches can identify useful patterns, and recent AI-based methods provide stronger semantic possibilities, but AI output is probabilistic and may be inaccurate. [3][5][7] These observations support a hybrid design in which deterministic analysis handles explicit structural mismatches and AI remains optional for tasks that benefit from broader language understanding.

### **2.4 Scientific Novelty and Need of the Work**

The contribution of IntelliDoc is best described as an integrated academic prototype rather than a claim of absolute novelty. The system combines deterministic Python AST-based documentation-drift detection with selective AI assistance and role-based documentation-quality oversight. The deterministic core makes each finding explainable, while the AI layer supplies assistance where structural rules have limited coverage. The role hierarchy extends the result from a local developer tool into a small team/project oversight system.

The need for the work arises because software documentation is an evolving artifact. Research has repeatedly examined documentation use, quality, consistency, and outdated references, which establishes the broader maintenance problem. [1][3][6] IntelliDoc narrows that problem into a practical workflow suitable for a student-scale web application and evaluates how far deterministic source-level analysis can go before AI assistance is useful.

### **2.5 Proposed System / Method of Solution**

The proposed solution is organized as a pipeline. A Programmer submits a Python codebase. The system discovers source files and parses them with Python AST. For each relevant function, the system extracts the signature, parameter names, docstring, and source-level return information where that information can be established. It then applies explicit comparison rules and records findings such as missing parameter documentation, obsolete parameter documentation, or other supported structural mismatches. A score is computed from documented, explainable indicators and the results are stored for historical analysis.

AI is invoked only through explicit actions. For a function without documentation, the Programmer may request a draft docstring. For a selected function, the Programmer may request the logical-consistency check. The AI output is displayed as advisory information and does not replace deterministic findings. If an AI provider becomes unavailable, the ordinary scanning pipeline remains operational.

## **CHAPTER 3: SYSTEM ANALYSIS AND DESIGN**

### **3.1 Requirement Specification**

The following functional requirements expand the project synopsis into a concise, testable specification. Requirement IDs are intentionally grouped by subsystem rather than split into an excessive number of micro-requirements. “Synopsis” identifies behaviour directly supported by the source synopsis; “Derived” identifies requirements introduced during detailed analysis.

| ID | Functional Requirement | Priority | Source |
| --- | --- | --- | --- |
| FR-AUTH-001 | The system shall authenticate a user before granting access to protected resources. | High | Synopsis |
| FR-AUTH-002 | The system shall associate each authenticated user with one of the roles Programmer, Team Lead, or Project Lead. | High | Synopsis |
| FR-AUTH-003 | The system shall enforce role-based authorization for dashboard and data access. | High | Synopsis |
| FR-SCAN-001 | The system shall allow a Programmer to initiate analysis of a Python codebase. | High | Synopsis |
| FR-SCAN-002 | The system shall discover Python source files within the submitted codebase and report files that cannot be parsed. | High | Derived |
| FR-AST-001 | The system shall parse supported Python source files using Python’s ast module. | High | Synopsis |
| FR-AST-002 | The system shall extract function/method names, parameters, docstrings, source locations, and relevant return information that is statically observable. | High | Derived |
| FR-DRIFT-001 | The system shall compare supported documentation structures with the actual function signature. | High | Synopsis |
| FR-DRIFT-002 | The system shall flag documentation that omits an actual function parameter. | High | Synopsis |
| FR-DRIFT-003 | The system shall flag documentation that refers to a parameter absent from the current signature. | High | Derived |
| FR-DRIFT-004 | The system shall report return-related inconsistencies only where they are deterministically supported by the implemented rules. | Medium | Derived |
| FR-MISSING-001 | The system shall identify functions that do not contain a docstring. | High | Synopsis |
| FR-AI-DOC-001 | The system shall allow a Programmer to request an AI-generated draft docstring for a function without documentation. | Medium | Synopsis |
| FR-AI-DOC-002 | The system shall present generated documentation as advisory content for Programmer review. | High | Derived |
| FR-AI-CHECK-001 | The system shall allow a Programmer to request an AI logical-consistency check for a selected function. | Medium | Synopsis |
| FR-AI-CHECK-002 | The system shall handle AI service failure without terminating deterministic scan results. | High | Synopsis |
| FR-SCORE-001 | The system shall compute an explainable documentation-reliability/code-quality metric for each Programmer and scan. | High | Synopsis |
| FR-HIST-001 | The system shall store scan history including summary metrics and findings. | Medium | Synopsis |
| FR-PROG-001 | The system shall provide the Programmer with scan results, findings, scores, and history. | High | Synopsis |
| FR-TEAM-001 | The system shall provide a Team Lead with authorized, aggregated metrics for programmers in the team. | High | Synopsis |
| FR-PROJ-001 | The system shall provide a Project Lead with authorized aggregated metrics across teams. | High | Synopsis |
| FR-API-001 | The backend shall expose authenticated endpoints for scans, findings, metrics, and optional AI actions. | High | Derived |

### **3.2 Non-Functional Requirements**

| ID | Non-Functional Requirement | Priority |
| --- | --- | --- |
| NFR-PER-001 | A moderate-sized codebase of approximately 5,000 to 10,000 lines should be processed quickly through deterministic checks. | High |
| NFR-PER-002 | AI calls shall not be invoked automatically for every function during a standard scan. | High |
| NFR-REL-001 | Deterministic analysis shall remain available when AI services are unavailable. | High |
| NFR-REL-002 | Parser or API failures shall be handled without crashing the entire application where recovery is possible. | High |
| NFR-SEC-001 | Protected resources shall require valid JWT authentication and role authorization. | High |
| NFR-SEC-002 | Secrets such as database and AI credentials shall be stored through environment configuration and not hard-coded. | High |
| NFR-SEC-003 | Source-code input shall be handled as potentially sensitive information. | High |
| NFR-USA-001 | Dashboards shall present understandable findings, metrics, and explanations without requiring tool-specific training. | Medium |
| NFR-MNT-001 | AI providers shall be accessed through a common abstraction so the provider can be changed without rewriting deterministic analysis. | High |
| NFR-MNT-002 | The analysis pipeline shall keep parsing, documentation comparison, and scoring logically separated. | High |

### **3.3 Information Collection / Requirements Elicitation**

The requirements were derived primarily from problem identification, the IntelliDoc synopsis, review of related documentation research, and analysis of the intended user roles. No claim is made that formal interviews or questionnaires were conducted because the supplied synopsis does not document such activities.

**Table 3.3: Information Gathering / Requirements Elicitation Methods**

| Method | Strengths | Limitations | Application to IntelliDoc |
| --- | --- | --- | --- |
| Project synopsis analysis | Provides a fixed scope, objectives, roles and technology baseline. | Does not by itself define every implementation detail. | Used as the primary source of requirements and project boundaries. |
| Academic literature review | Provides evidence about documentation use, consistency and maintenance. | Research contexts may differ from a student-scale prototype. | Used to establish problem background and identify established approaches. |
| Review of existing documentation/static-analysis approaches | Shows common patterns for documentation generation and analysis. | Tools differ in languages and supported semantics. | Used to shape the deterministic and optional AI layers. |
| Iterative design/prototyping | Helps refine workflows and error handling. | Design assumptions still require validation during implementation. | Used as a proposed refinement method for scan, findings and dashboards. |

### **3.4 Analysis and Development of the Actual Solution**

The analysis decomposes IntelliDoc into independent but connected stages. The frontend is responsible for presenting roles, scans, findings and dashboards. FastAPI provides authenticated application services. The analysis layer processes Python source code through AST. The drift detector applies deterministic rules to extracted function and documentation information. The scoring engine turns stored findings into explainable metrics. PostgreSQL persists users, teams/projects, scan records, findings, AI analyses, and scores. AI providers are accessed through an abstraction layer so their availability does not determine whether the core scan succeeds.

The design also separates data that is safe to expose to different roles. A Programmer receives their own detailed results. A Team Lead receives authorized team-level information. A Project Lead receives higher-level aggregated information. The model is intentionally narrower than general performance management: the score reflects documentation-related evidence produced by IntelliDoc and is not a measure of total developer competence.

### **3.5 Description of Various Modules**

**Table 3.4: IntelliDoc Modules**

| Module | Responsibility | Input | Output |
| --- | --- | --- | --- |
| Authentication and RBAC | Validates credentials, creates/validates JWTs, and applies role-based authorization. | Credentials / token | Authenticated identity and access decision |
| Codebase / Scan Management | Accepts scan requests, manages scan status, and coordinates source analysis. | Python codebase | Scan record and analysis output |
| AST Parsing | Parses Python source and exposes source-level structure. | Python files | AST nodes / function metadata |
| Documentation Analysis | Extracts and normalizes docstrings and supported documentation sections. | Function metadata / docstrings | Comparable documentation structures |
| Drift Detection | Applies deterministic comparison rules and assigns finding types/severity. | Code/documentation facts | Explainable findings |
| Missing Documentation | Identifies functions without docstrings. | Function metadata | Missing-documentation findings |
| AI Documentation Generation | Requests a draft docstring for an undocumented function. | Function context | AI-generated draft |
| AI Logical-Consistency Check | Requests deeper advisory analysis for a selected function. | Function + documentation context | Advisory AI result |
| Scoring | Aggregates documented indicators into an explainable score. | Findings / function counts | Programmer/scan score |
| Scan History | Persists and retrieves previous scan summaries and findings. | Scan data | Historical records |
| Programmer Dashboard | Presents detailed scan results and personal metrics. | Stored scan data | Interactive results |
| Team Lead Dashboard | Aggregates authorized programmer metrics. | Programmer scores | Team overview |
| Project Lead Dashboard | Aggregates team/project metrics. | Team scores | Project overview |
| API / Database Layer | Provides persistence and authenticated REST services. | Application requests | JSON responses / database state |

### **3.6 System Development Tools**

**Table 3.5: System Development Tools**

| Tool / Environment | Purpose |
| --- | --- |
| VS Code | Primary development environment for frontend, backend, diagrams, and documentation. |
| Git / GitHub | Version control and source management. |
| Python | Backend implementation and source-code analysis. |
| FastAPI | REST API and service layer. |
| Next.js / React / TypeScript | Web frontend and dashboard implementation. |
| PostgreSQL | Persistent data storage. |
| Draw.io / diagrams.net | Diagram preparation and refinement. |
| Web/API testing tools | Manual and automated API verification during implementation. |

### **3.7 Choice of Language**

Python is appropriate for IntelliDoc because the core project requirement is Python source analysis, and Python provides the ast module as a standard source-parsing mechanism. FastAPI provides a lightweight Python web framework for the backend. TypeScript is used on the frontend to provide typed development over React and Next.js. This division keeps source-code analysis close to the language being inspected while allowing a modern web interface for dashboards.

### **3.8 Choice of System for Implementation**

A web application was selected because the project has three role levels and several dashboards that benefit from centralized access. Next.js and React provide the presentation layer, FastAPI provides application services, and PostgreSQL provides structured persistence. JWT supports stateless authenticated requests. Groq and Gemini are kept behind a common AI abstraction so that the deterministic analysis remains decoupled from external model providers.

### **3.9 System Architecture**

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_01.png)

Fig. 3.1: IntelliDoc System Architecture

The architecture follows a layered design. Presentation concerns remain in the frontend, access control and orchestration are handled by FastAPI, analysis modules perform source inspection, and PostgreSQL stores durable records. The AI branch is connected as an optional service from the application/analysis layer. This arrangement reflects the central design rule that deterministic analysis is the baseline service and AI is a secondary capability.

### **3.10 Detailed Design Diagrams**

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_02.png)

Fig. 3.2: IntelliDoc Use Case Diagram

The use case model emphasizes the Programmer as the primary operational actor, while Team Lead and Project Lead receive progressively aggregated information. AI Services act as external supporting services for explicitly requested AI functionality.

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_03.png)

Fig. 3.3: DFD Level 0 (Context Diagram)

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_04.png)

Fig. 3.4: DFD Level 1 : IntelliDoc Processing and Data Flow

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_05.png)

Fig. 3.5: ER Diagram : IntelliDoc PostgreSQL Logical Model

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_06.png)

Fig. 3.6: Activity Diagram : IntelliDoc Main Scan Workflow

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_07.png)

Fig. 3.7: Sequence Diagram : Codebase Scan

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_08.png)

Fig. 3.8: Sequence Diagram : Optional AI Assistance

![Embedded image or diagram](assets/IntelliDoc_SRS_Project_Report_Updated_image_09.png)

Fig. 3.9: Class Diagram : IntelliDoc Core Software Model

### **3.11 Key Algorithms**

#### Algorithm 1 : Source File Discovery

Input: codebase directory. Traverse the submitted project, identify Python source files, ignore unsupported file types, and record files that cannot be accessed. Output: list of candidate source files.

#### Algorithm 2 : AST Parsing

Input: Python source file. Read the source, call Python ast parsing, and construct an abstract syntax tree. On syntax failure, record a parse error associated with the file and continue where possible.

#### Algorithm 3 : Function Extraction

Input: AST. Traverse function and async-function nodes and collect function name, source location, signature, and docstring availability. Nested functions may be represented where supported by the traversal policy.

#### Algorithm 4 : Docstring Extraction

Input: function node. Read the node-level docstring, identify supported Google-style sections such as Args and Returns, and normalize names for comparison.

#### Algorithm 5 : Signature/Documentation Comparison

Input: function signature and normalized documentation. Compare actual parameter names with documented parameter names. Identify missing or obsolete documentation entries and record explanations.

#### Algorithm 6 : Drift Detection

Input: normalized comparison result. Apply deterministic rules and assign finding type/severity. Only rules whose evidence is available in source-level information are reported deterministically.

#### Algorithm 7 : Missing Documentation Detection

Input: functions. Mark functions without docstrings as missing-documentation findings. These are kept conceptually distinct from stale documentation findings.

#### Algorithm 8 : AI Documentation Generation

Input: selected undocumented function. Send minimal necessary context through the AI abstraction to the configured Groq model, receive a draft, validate/display it as advisory content, and leave acceptance/rejection to the Programmer.

#### Algorithm 9 : AI Logical-Consistency Check

Input: selected function and documentation. Send the relevant context to Gemini through the AI abstraction, display the returned advisory assessment, and store the analysis state. Failure does not invalidate deterministic findings.

#### Algorithm 10 : Score Calculation

Input: scan-level deterministic findings and completeness indicators. Normalize the selected components into a 0 to 100 metric according to the documented scoring policy. Store both the score and component breakdown.

#### Algorithm 11 : Team Aggregation

Input: authorized Programmer scores. Aggregate according to a documented rule such as weighted mean by analysed-function count. Preserve access boundaries.

#### Algorithm 12 : Project Aggregation

Input: authorized Team-level aggregates. Combine team metrics to create a project-level view while preserving the separation between detailed programmer records and higher-level summaries.

### **3.12 Use Case Specifications**

| ID | Use Case | Actor | Preconditions | Main Flow | Alternate / Exception | Postcondition |
| --- | --- | --- | --- | --- | --- | --- |
| UC-01 | Login | Programmer / Team Lead / Project Lead | Valid account exists | Enter credentials to validate to issue JWT to open role dashboard. | Invalid credentials or expired token to access denied. | Authenticated session |
| UC-02 | Scan Codebase | Programmer | Authenticated Programmer | Select codebase to submit to parse source to analyse functions to detect findings to calculate score to store/display results. | Syntax/file error to record error and continue where possible. | Scan results available |
| UC-03 | Analyse Documentation | System | Active scan | Extract function signature and documentation to normalize to compare using deterministic rules. | Unsupported documentation structure to report supported checks only. | Findings generated |
| UC-04 | View Findings | Programmer | Completed/partial scan | Open scan to filter/select finding to view explanation and function location. | No findings to show clean result state. | Finding details viewed |
| UC-05 | Generate AI Documentation Draft | Programmer | Function lacks docstring | Select function to request draft to AI response to display draft to review. | AI unavailable to show failure; deterministic scan remains intact. | Draft reviewed |
| UC-06 | Review AI Draft | Programmer | AI draft displayed | Edit / accept / reject draft. | Unexpected content to reject/edit manually. | Review decision recorded if implemented |
| UC-07 | AI Logical-Consistency Check | Programmer | Selected function and documentation | Request check to send context to receive advisory result to display. | AI failure/timeout to show advisory error. | Advisory analysis displayed |
| UC-08 | View Scan History | Programmer | Existing scans | Open history to select scan to view summary/findings/score. | No history to empty-state message. | Historical scan viewed |
| UC-09 | View Programmer Metrics | Programmer / Team Lead | Authorized data | Open dashboard to view score components and trends. | Unauthorized record to access denied. | Metrics displayed |
| UC-10 | View Team Metrics | Team Lead | Authorized team membership | Open team dashboard to view programmers and aggregated metrics. | No authorized programmers to empty state. | Team metrics displayed |
| UC-11 | View Project Metrics | Project Lead | Authorized project teams | Open project dashboard to view team aggregates and trends. | Unauthorized team to not shown. | Project metrics displayed |

### **3.13 Database Design and Data Dictionary**

**Table 3.7: Data Entities**

| Entity | Purpose | Key Attributes |
| --- | --- | --- |
| User | Stores authenticated identities and role membership. | user_id, name, email, password_hash, role, team_id, created_at |
| Team | Represents an organizational team. | team_id, team_name, team_lead_id |
| Project | Represents a project grouping teams/codebases. | project_id, project_name, project_lead_id |
| Codebase | Represents a codebase submitted for analysis. | codebase_id, name, owner_id, project_id |
| Scan | Stores an individual analysis run. | scan_id, codebase_id, initiated_by, timestamp, status, summary |
| SourceFile | Stores source-file metadata for a scan. | file_id, scan_id, path, parse_status |
| Function | Stores extracted function information. | function_id, file_id, name, line_number, signature, docstring |
| DocumentationFinding | Stores deterministic documentation findings. | finding_id, function_id, type, severity, explanation |
| AIAnalysis | Stores optional AI analysis records. | analysis_id, function_id, provider, analysis_type, result, timestamp, status |
| Score | Stores scan-level score and component breakdown. | score_id, scan_id, programmer_id, documentation_score, code_quality_score, breakdown |

#### **3.13.1 Data Dictionary**

**Table 3.8: Data Dictionary**

| Entity | Field | Type | Constraints / Description |
| --- | --- | --- | --- |
| User | user_id | UUID / integer | Primary key; unique |
| User | role | ENUM / varchar | Programmer, Team Lead, Project Lead |
| User | team_id | FK | References Team; nullable only where project design permits |
| Team | team_lead_id | FK | References User |
| Project | project_lead_id | FK | References User |
| Codebase | owner_id | FK | References User |
| Scan | status | varchar | Queued, Running, Completed, Partial, Failed |
| Function | name | varchar | Function or method name |
| Function | line_number | integer | Source location; non-negative |
| Finding | type | varchar | Supported deterministic finding type |
| Finding | severity | varchar | High, Medium, Low as configured |
| AIAnalysis | provider | varchar | Groq or Gemini |
| AIAnalysis | status | varchar | Requested, Completed, Failed |
| Score | documentation_score | decimal | Normalized 0 to 100 metric |

Data integrity rules include unique identifiers, valid role values, valid finding and severity types, foreign-key consistency, score range validation, and authorization checks based on ownership or role. Source-code content and AI responses should be handled as potentially sensitive data. Detailed schema decisions such as UUID versus integer keys are implementation-level choices and should be marked as proposed design decisions during development if not already fixed.

#### **3.13.2 User Access Matrix**

**Table 3.9: User Access Matrix**

| Role | Own Scan Details | Team Programmer Metrics | Team Aggregates | Project Aggregates |
| --- | --- | --- | --- | --- |
| Programmer | Yes | No | Own/team-authorized summary only if explicitly granted | No |
| Team Lead | Authorized team | Yes | Yes | No |
| Project Lead | Authorized project as required | Authorized higher-level view | Yes | Yes |

### **3.14 Technology Stack Justification**

**Table 3.10: Technology Stack Justification**

| Component | Technology | Justification |
| --- | --- | --- |
| Frontend | Next.js + React + TypeScript | Suitable for a structured web interface with multiple role-based dashboards and typed client-side logic. |
| Backend | Python + FastAPI | Keeps source-code analysis and web services in the same language and provides a lightweight REST service. |
| Static Analysis | Python ast | Provides deterministic access to Python source structure and supports explainable rules. |
| Database | PostgreSQL | Provides relational integrity for users, teams, projects, scans, findings, AI records, and scores. |
| AI : Documentation | Groq / Llama 3.3 70B | Used selectively for draft documentation when documentation is missing, subject to free-tier availability in the project plan. |
| AI : Consistency | Google Gemini Flash | Used on demand for a deeper advisory consistency check. |
| Authentication | JWT | Provides token-based authentication suitable for a web API with role claims. |
| Version Control | Git / GitHub | Supports source management and project history. |
| Deployment | Vercel + Render/Railway | Matches the free-tier-oriented deployment plan in the synopsis. |

### **3.15 Design Tools and Limitations**

UML, DFD, ER, architecture, activity, sequence, and class diagrams may be prepared using Draw.io/diagrams.net, Mermaid, PlantUML, Graphviz, or another standards-oriented modelling tool. The diagrams in this document are intentionally simple and academic in appearance. The choice of tool does not change the underlying notation.

The major design limitation is static-analysis coverage. AST provides structural information, but it cannot fully determine arbitrary runtime behaviour, side effects, dynamic attribute access, reflection, external service responses, or every semantic relationship between a function and its prose description. Consequently, IntelliDoc reports only deterministic findings supported by implemented rules and uses AI for an optional broader opinion. A second limitation is score interpretation: an explainable documentation metric should not be treated as a general assessment of a programmer or a complete code-quality proof.

## **CHAPTER 4: SYSTEM IMPLEMENTATION**

### **4.1 Hardware Requirements**

The project does not require specialized hardware. A normal development computer capable of running a modern web browser, Python, Node.js tooling, and PostgreSQL is sufficient. A practical student development environment may use a multi-core processor, at least 8 GB RAM, and sufficient storage for source code, dependencies, database data, and test projects. These are practical recommendations rather than measurements specified by the synopsis.

| Component | Recommended Baseline | Purpose |
| --- | --- | --- |
| Processor | Dual-core or better | Frontend/backend development and analysis tasks |
| RAM | 8 GB or more recommended | IDE, browser, backend, database and test projects |
| Storage | 20 GB free space or more | Dependencies, database, source code and build artifacts |
| Display | 1366 × 768 or better | Dashboard and code-view usability |
| Network | Internet access when AI/remote deployment services are used | AI APIs, package installation and deployment |

### **4.2 Software Requirements**

| Software | Requirement / Use |
| --- | --- |
| Operating System | Windows or Linux development environment compatible with Python and Node.js |
| Browser | Current Chrome, Firefox, Edge or equivalent modern browser |
| Python | Required for FastAPI backend and AST analysis |
| Node.js / npm | Required for Next.js frontend and related tooling |
| Next.js / React / TypeScript | Frontend and dashboards |
| FastAPI | Backend API |
| PostgreSQL | Persistent database |
| Git / GitHub | Version control |
| Groq / Gemini access | Optional AI capabilities subject to configured credentials and provider availability |

### **4.3 Input Requirements**

The system receives several types of input. Authentication requests contain user credentials. Scan requests contain a Python codebase or codebase reference. Deterministic analysis consumes Python source files. Optional AI actions consume a selected function and the minimum source/documentation context required for the requested action. Dashboard requests contain authenticated user context and filters such as scan selection. All inputs should be validated before processing.

#### **4.3.1 Codebase Input**

- Python source files and supported project structure.

- The source should be readable by the analysis process.

- Unsupported file types should be ignored or excluded from deterministic analysis.

- Files with syntax errors should produce localized parser errors rather than silently disappearing.

### **4.4 Operation Manual**

#### **4.4.1 Programmer Workflow**

1. Log in using valid credentials.

1. Open the scan interface.

1. Select or provide the Python codebase.

1. Start the scan.

1. Review the scan summary and number of analysed functions.

1. Open findings to inspect the affected file/function and explanation.

1. For functions without documentation, optionally request an AI-generated draft.

1. Review, edit, accept, or reject the draft as appropriate.

1. For a selected function, optionally request the AI logical-consistency check.

1. Review documentation-reliability/code-quality metrics and historical scan information.

#### **4.4.2 Team Lead Workflow**

1. Log in.

1. Open the Team Lead dashboard.

1. Review the authorized programmers in the team.

1. Inspect aggregated documentation-reliability and related quality metrics.

1. Open authorized programmer details when a deeper review is required.

#### **4.4.3 Project Lead Workflow**

1. Log in.

1. Open the Project Lead dashboard.

1. Review aggregated team metrics.

1. Inspect authorized historical trends.

1. Use available drill-down features without accessing unrelated project data.

#### **4.4.4 Error Handling / Troubleshooting**

**Table 4.3: Troubleshooting and Error Handling**

| Problem | Likely Cause | Expected System Behaviour / Action |
| --- | --- | --- |
| Login rejected | Invalid credentials or token | Display authentication error and deny protected access. |
| Python file cannot be parsed | Syntax error | Record parse failure for the file and continue with other files where possible. |
| No drift findings | Code is consistent under current rules | Show a clean result state; do not imply perfect semantic correctness. |
| AI draft unavailable | Provider error, timeout or quota | Display an advisory failure and keep deterministic results available. |
| Dashboard data unavailable | API/database problem | Show an error state and preserve the rest of the usable application. |
| Unauthorized dashboard access | Role or ownership mismatch | Reject the request and do not expose protected data. |

### **4.5 Output Reports / Results**

The primary system output is a scan result containing a summary of the analysed codebase and detailed documentation findings. A function-level result identifies the file, function, finding type, severity and explanation. Additional outputs include missing-documentation indicators, scores, scan-history records, AI drafts, and AI consistency assessments. Team Lead and Project Lead dashboards present these results at progressively aggregated levels according to authorization.

**Table 4.4: Output Reports / Results**

| Output | Description |
| --- | --- |
| Scan Summary | Files analysed, functions analysed, documented/undocumented counts, findings, and overall score. |
| Finding List | Deterministic findings grouped by type and severity. |
| Function Detail | Function metadata, signature/documentation information and explanation. |
| AI Draft | Advisory generated docstring for a function lacking documentation. |
| AI Consistency Result | Advisory result for a manually selected function. |
| Programmer Metrics | Documentation-reliability and related quality indicators with history. |
| Team Metrics | Aggregated authorized programmer metrics. |
| Project Metrics | Aggregated team/project metrics. |

### **4.6 Implementation Status**

The supplied IntelliDoc synopsis is a project synopsis and does not provide a verified implementation-completion table, measured benchmark results, or deployment evidence. Therefore, this document intentionally does not assign a completion percentage or claim that the system is already implemented. The report should be updated during development with actual module status, screenshots, test results, and deployment evidence once those artifacts exist.

**Table 4.5: Implementation Status**

| Area | Status in this document |
| --- | --- |
| Requirements specification | Specified |
| Architecture and design | Specified |
| Data model | Proposed / specified at logical level |
| Implementation code | Not evidenced by the supplied synopsis |
| Measured performance | Not yet evidenced |
| Deployment status | Not yet evidenced |
| Empirical user evaluation | Not yet evidenced |

## **CHAPTER 5: RESULT AND DISCUSSION**

### **5.1 Evaluation Framework and Interpretation of Results**

Actual measured results are not included because the supplied synopsis does not contain experimental measurements. The following framework defines how the implemented system should be evaluated. It is preferable to report a small number of reliable measurements rather than inventing completion percentages or performance claims.

**Table 5.1: Evaluation Framework**

| Evaluation Area | Measure | Interpretation |
| --- | --- | --- |
| Parsing coverage | Files successfully parsed / files submitted | Shows how robust source processing is for valid and invalid inputs. |
| Documentation coverage | Functions with docstrings / total functions | Shows completeness of documentation in the evaluated codebase. |
| Drift detection | Number and type of deterministic findings | Shows the kinds of documentation mismatches the rules identify. |
| Rule precision sample | Manually reviewed subset of findings | Estimates how often reported findings are valid within the test sample. |
| Scan performance | Elapsed deterministic scan time for selected codebase sizes | Checks the moderate-size performance objective. |
| AI utility | Human review of draft usefulness/correctness | Evaluates the supplementary AI features. |
| Reliability | Successful scans under simulated AI/API failures | Checks whether deterministic analysis remains usable. |
| Role security | Authorized and unauthorized access tests | Checks whether data visibility follows the role model. |

A suitable evaluation dataset should include deliberately constructed examples with correct documentation, missing documentation, obsolete parameter documentation, parameter-name mismatches, and return-related cases supported by the implemented rules. The same dataset can be reused to compare deterministic findings with a manually verified expected result.

### **5.2 Application Areas and Scope of Work**

IntelliDoc can be applied as an internal development-support tool for Python projects where docstrings are an important part of maintainability. It can also serve educational projects where instructors or team leads want a structured view of documentation quality. The first release remains intentionally narrower than a general code-quality platform: its “code-quality oversight” is centered on documentation-related evidence and does not attempt to replace general static analyzers, test frameworks, bug trackers, or continuous-integration systems.

### **5.3 Discussion**

The expected value of IntelliDoc comes from combining low-cost deterministic checks with optional higher-level AI assistance. Deterministic findings can be explained directly in terms of source-level facts, which supports trust and debugging. AI can help when the user wants natural-language generation or a broader semantic opinion, but that benefit is balanced by the possibility of inaccurate or incomplete outputs. The hybrid architecture therefore creates a clear boundary: the system can still produce a useful scan even if AI is unavailable.

One important consideration is false positives and false negatives. A rule may correctly identify a structural mismatch while still missing a semantic meaning difference. Conversely, a documentation structure that appears inconsistent to a simple rule may be intentionally written in a style that the current parser does not understand. These limitations should be evaluated with representative test cases rather than hidden behind a single score. The same principle applies to role-level scores: aggregates are useful for visibility, but the underlying findings remain necessary to understand what caused the metric to change.

## **CHAPTER 6: CONCLUSION**

### **6.1 Advantages and Special Features of the System**

- Deterministic AST-based analysis provides an explainable baseline for documentation-drift detection.

- The system distinguishes missing documentation from existing but inconsistent documentation.

- AI documentation generation reduces the effort required to create a starting draft for undocumented functions.

- The optional AI logical-consistency check provides deeper advisory analysis without making AI mandatory.

- Role-based dashboards turn scan-level findings into programmer-, team-, and project-level visibility.

- Scan history enables comparison of documentation quality across multiple analyses.

- The AI abstraction allows providers to be changed without redesigning the deterministic pipeline.

- The first release remains focused on Python and avoids unnecessary expansion into general-purpose bug detection.

### **6.2 Limitations**

- The first release supports Python only.

- AST analysis cannot fully infer arbitrary runtime semantics or prove that documentation is semantically correct.

- AI-generated documentation and AI consistency assessments may contain errors.

- The current scope does not include automatic whole-codebase AI reasoning.

- Git-history-based identification of when drift began is outside the first release.

- CI/CD integration is outside the first release.

- The score reflects documentation-related quality evidence and is not a general measure of developer ability or complete software quality.

- Free-tier AI availability and provider limits may constrain optional AI features.

### **6.3 Future Extensions**

- Git/GitHub integration for repository-aware analysis and historical drift timing.

- CI/CD integration to detect documentation issues during pull requests or builds.

- IDE extensions for near-real-time developer feedback.

- Additional programming-language parsers.

- Support for additional documentation styles beyond the initial Google-style focus.

- Richer semantic analysis using program analysis and carefully controlled AI methods.

- More detailed trend analysis and configurable team/project reporting.

## **REQUIREMENTS TRACEABILITY**

**Table 5.2: Requirements Traceability Matrix**

| Requirement Area | SRS IDs | Design Component | Diagram | Tests |
| --- | --- | --- | --- | --- |
| Project scanning | FR-SCAN-001, FR-SCAN-002 | Codebase / Scan Management | Fig. 3.1, Fig. 3.4, Fig. 3.7 | T-03, T-04 |
| AST analysis | FR-AST-001, FR-AST-002 | AST Parsing | Fig. 3.1, Fig. 3.4 | T-05, T-06 |
| Documentation drift | FR-DRIFT-001..004 | Documentation Analysis / Drift Detector | Fig. 3.4, Fig. 3.6 | T-07..T-10 |
| Missing documentation | FR-MISSING-001 | Missing Documentation Module | Fig. 3.6 | T-11 |
| AI draft | FR-AI-DOC-001, FR-AI-DOC-002 | AI Service | Fig. 3.8 | T-12, T-13 |
| AI consistency | FR-AI-CHECK-001, FR-AI-CHECK-002 | AI Service | Fig. 3.8 | T-14 |
| Scoring | FR-SCORE-001 | Scoring Engine | Fig. 3.1, Fig. 3.9 | T-15 |
| History | FR-HIST-001 | Scan History / Database | Fig. 3.5 | T-16 |
| Role dashboards | FR-PROG-001, FR-TEAM-001, FR-PROJ-001 | Dashboard Modules / RBAC | Fig. 3.2 | T-17..T-19 |
| API | FR-API-001 | FastAPI / Database | Fig. 3.1, Fig. 3.4 | T-20 |

## **RISKS AND LIMITATIONS**

**Table 5.3: Risk Register**

| Risk | Probability | Impact | Mitigation |
| --- | --- | --- | --- |
| AI provider unavailable | Medium | Medium | Keep deterministic scanning independent; show advisory error for AI features. |
| Free-tier quota exhausted | Medium | Medium | Use AI only on demand and expose graceful failure. |
| AI output inaccurate | Medium | High | Label results advisory; require Programmer review. |
| AST cannot establish semantic intent | High | Medium | Limit deterministic rules to source-level evidence and document limitations. |
| Malformed Python source | Medium | Medium | Record localized parse errors and continue with other files when possible. |
| Source-code confidentiality | Medium | High | Minimize context sent to AI; use secure transport and environment-based credentials. |
| Database failure | Low/Medium | High | Handle errors gracefully and preserve client state where feasible. |
| Unauthorized data access | Low | High | Use JWT, RBAC, ownership checks and protected API routes. |
| Large codebase slows scan | Medium | Medium | Keep deterministic analysis efficient; measure performance during testing. |
| Score interpreted as overall developer quality | Medium | Medium | Document the score as a documentation-related analytical metric only. |

## **REFERENCES**

[1] T. C. Lethbridge, J. Singer, and A. Forward, “How software engineers use documentation: the state of the practice,” IEEE Software, vol. 20, no. 6, pp. 35 to 39, 2003. DOI: 10.1109/MS.2003.1241364.

[2] S. C. B. de Souza, N. Anquetil, and K. M. de Oliveira, “Which Documentation for Software Maintenance?,” Journal of the Brazilian Computer Society, vol. 12, no. 3, pp. 31 to 44, 2006. DOI: 10.1007/BF03194494.

[3] N. Khamis, J. Rilling, and R. Witte, “Assessing the quality factors found in in-line documentation written in natural language: The JavadocMiner,” Data & Knowledge Engineering, vol. 87, pp. 19 to 40, 2013. DOI: 10.1016/j.datak.2013.02.001.

[4] T. Kuhn and A. Bergel, “Verifiable source code documentation in controlled natural language,” Science of Computer Programming, vol. 96, pp. 121 to 140, 2014. DOI: 10.1016/j.scico.2014.01.002.

[5] M. P. Arthur, “Automatic Source Code Documentation using Code Summarization Technique of NLP,” Procedia Computer Science, vol. 171, pp. 2522 to 2531, 2020. DOI: 10.1016/j.procs.2020.04.273.

[6] W. S. Tan, M. Wagner, and C. Treude, “Detecting outdated code element references in software repository documentation,” Empirical Software Engineering, vol. 29, no. 1, Article 5, 2024. DOI: 10.1007/s10664-023-10397-6.

[7] T. Kiecker, J. A. Sparka, M. Reuter, A. Ziegler, and L. Grunske, “CASCADE: Detecting Inconsistencies between Code and Documentation with Automatic Test Generation,” Proceedings of the ACM on Software Engineering, FSE, 2026. DOI: 10.1145/3808175.

[8] Python Software Foundation, “ast : Abstract Syntax Trees,” Python Documentation. Available from the official Python documentation.

[9] Google, “Google Python Style Guide,” Google Developers. Available from the official Google style guide documentation.

[10] Sebastián Ramírez, “FastAPI Documentation,” FastAPI official documentation.

[11] Groq, “Groq API Documentation,” official Groq documentation.

[12] Google, “Gemini API Documentation,” Google AI for Developers.

[13] PostgreSQL Global Development Group, “PostgreSQL Documentation,” official PostgreSQL documentation.

[14] Next.js, “Next.js Documentation,” official Next.js documentation.

[15] React, “React Documentation,” official React documentation.

## **APPENDIX A: CONFIGURATION PARAMETERS**

Values in this appendix are proposed defaults unless explicitly defined by the synopsis. They should be finalized during implementation and testing.

**Table A.1: Configuration Parameters**

| Parameter | Proposed Default | Purpose |
| --- | --- | --- |
| MAX_SOURCE_SIZE | Project-defined during implementation | Prevents unexpectedly large uploads from overwhelming the scan process. |
| AI_TIMEOUT | 30 seconds proposed | Bounds waiting time for optional AI requests. |
| MAX_AI_CONTEXT | Project-defined truncation strategy | Limits the amount of source context sent externally. |
| SEVERITY_LEVELS | High / Medium / Low | Provides consistent finding labels. |
| SCORE_RANGE | 0 to 100 | Normalizes reporting across scans. |
| AI_PROVIDER_DOCUMENTATION | Groq | Provider for draft docstring generation in the synopsis. |
| AI_PROVIDER_CONSISTENCY | Gemini | Provider for logical-consistency checks in the synopsis. |
| DB_CONNECTION | Environment variable | Keeps database credentials outside source control. |

## **APPENDIX B: DRAFT API SPECIFICATION**

**Table B.1: Draft API Specification**

| Method | Endpoint | Purpose | Authentication | Role |
| --- | --- | --- | --- | --- |
| POST | /auth/login | Authenticate user and issue JWT | No | All |
| POST | /scans | Create/start a scan | JWT | Programmer |
| GET | /scans | List authorized scans | JWT | Programmer / Lead |
| GET | /scans/{scan_id} | Retrieve scan summary | JWT | Authorized users |
| GET | /scans/{scan_id}/findings | Retrieve findings | JWT | Authorized users |
| GET | /functions/{function_id} | Retrieve function detail | JWT | Authorized users |
| POST | /functions/{function_id}/generate-doc | Request AI documentation draft | JWT | Programmer |
| POST | /functions/{function_id}/consistency-check | Request AI consistency check | JWT | Programmer |
| GET | /scores/me | Programmer metrics | JWT | Programmer |
| GET | /team/scores | Team metrics | JWT | Team Lead |
| GET | /project/scores | Project metrics | JWT | Project Lead |

This appendix is a proposed API baseline, not a statement that these endpoints have already been implemented. Exact response schemas, pagination and error objects should be finalized during implementation.

## **APPENDIX C: SCORING RULES**

The synopsis requires an explainable documentation-reliability and code-quality score but does not define exact numerical weights. The following is therefore a PROPOSED / DERIVED scoring model that should be validated during implementation.

For each scan, the Documentation Reliability Score (DRS) is normalized to 100 points using three components: Completeness (40 points), Parameter/Structure Consistency (40 points), and Return/Other Supported Consistency (20 points). Missing documentation reduces completeness. Deterministic findings reduce the relevant consistency component according to severity. AI advisory findings are displayed separately and do not automatically alter the deterministic score unless a future validated policy explicitly chooses to do so.

Proposed calculation: Completeness = 40 × (documented_functions / total_functions). Consistency components begin at their maximum and receive bounded penalties for deterministic findings. Final DRS = bounded sum of component scores between 0 and 100. Team and project metrics are computed from authorized programmer/scan metrics using a documented aggregation rule. Exact penalty values are PROPOSED and must be tuned using validation data rather than assumed to be scientifically optimal.

Worked example: suppose a scan contains 100 functions and 80 are documented. Completeness contributes 40 × 0.80 = 32 points. If deterministic consistency rules produce bounded penalties totaling 10 points from the remaining 60 available points, the resulting score would be 82/100. The example is illustrative only; the final weighting policy should be verified against representative test cases.

## **APPENDIX D: EXAMPLE ANALYSIS RESULTS**

Example 1 : Missing Parameter Documentation

Input function:

def calculate_total(price, tax):
 """
 Calculate the total price.

 Args:
 price: Base price.

 Returns:
 Total price including tax.
 """
 return price + tax

Possible deterministic finding: The function signature contains the parameter “tax”, but the docstring does not document it. Finding type: Missing Parameter Documentation. Severity: Medium (proposed).

Example 2 : Obsolete Parameter Documentation

If the signature is def calculate_total(price, tax): but the docstring documents an argument named discount that no longer exists, IntelliDoc can report obsolete parameter documentation because the documented name is absent from the current signature.

Example 3 : Missing Documentation

If a function has no docstring, IntelliDoc reports a missing-documentation finding. The Programmer may request an AI-generated draft, but the generated result remains advisory until reviewed by the Programmer.

Example 4 : AI Logical-Consistency Check

A Programmer may select a documented function and request a deeper AI analysis. The result may indicate that the documentation appears consistent, inconsistent, or uncertain, together with an explanation. Such an output is advisory and is not treated as a proof of program correctness.
