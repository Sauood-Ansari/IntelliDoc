"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { LogOut, Plus, RefreshCw } from "lucide-react";
import { api, Codebase, Metrics, Project, Scan, Team, User } from "@/lib/api";
import { SignIn } from "@/components/sign-in";
import { Organization } from "@/components/organization";
import { MembershipAccess } from "@/components/membership-access";
import { UploadScan } from "@/components/upload-scan";
import { dateText, ScanResults, scoreText, ScoringGuide, Status } from "@/components/scan-results";

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [booting, setBooting] = useState(true);
  useEffect(() => {
    api<User>("/auth/me").then(setUser).catch(() => {}).finally(() => setBooting(false));
    function expired() { setUser(null); }
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);
  if (booting) return <main className="boot" role="status">Opening IntelliDoc…</main>;
  if (!user) return <SignIn onSignedIn={setUser} />;
  return <Workspace key={user.user_id} user={user} onSignedOut={() => setUser(null)} />;
}

function Workspace({ user, onSignedOut }: { user: User; onSignedOut: () => void }) {
  const programmer = user.role === "Programmer";
  const projectLead = user.role === "Project Lead";
  const setupView = projectLead ? "Projects" : "Teams";
  const [view, setView] = useState(programmer ? "Memberships" : setupView);
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [scopeId, setScopeId] = useState("");
  const [organizationLoading, setOrganizationLoading] = useState(!programmer);
  const [scans, setScans] = useState<Scan[]>([]);
  const [codebases, setCodebases] = useState<Codebase[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({});
  const [selected, setSelected] = useState<Scan | null>(null);
  const [upload, setUpload] = useState(false);
  const [uploadBase, setUploadBase] = useState("");
  const [loading, setLoading] = useState(false);
  const [moreLoading, setMoreLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const moreRequest = useRef<AbortController | null>(null);
  const reload = useCallback(() => setRefresh(value => value + 1), []);
  const filterQuery = !programmer && scopeId ? `${projectLead ? "project_id" : "team_id"}=${scopeId}` : "";

  useEffect(() => {
    if (programmer) return;
    const controller = new AbortController();
    setOrganizationLoading(true);
    const endpoint = projectLead ? "/projects?owned=true" : "/teams?owned=true";
    api<(Project | Team)[]>(endpoint, { signal: controller.signal }).then(records => {
      if (projectLead) setProjects(records as Project[]);
      else setTeams(records as Team[]);
      const ids = records.map(record => "team_id" in record ? record.team_id : record.project_id);
      setScopeId(previous => ids.includes(previous) ? previous : ids[0] || "");
    }).catch(exception => { if (!controller.signal.aborted) setError(exception.message); })
      .finally(() => { if (!controller.signal.aborted) setOrganizationLoading(false); });
    return () => controller.abort();
  }, [programmer, projectLead, refresh]);

  useEffect(() => {
    moreRequest.current?.abort();
    setMoreLoading(false);
    if (!programmer && !scopeId) {
      setScans([]); setCodebases([]); setMetrics({}); setHasMore(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true); setError("");
    const metricsPath = programmer ? "/scores/me" : projectLead ? `/project/scores?project_id=${scopeId}` : `/team/scores?team_id=${scopeId}`;
    Promise.all([
      api<Scan[]>(`/scans?limit=50&${filterQuery}`, { signal: controller.signal }),
      api<Codebase[]>(`/codebases?${filterQuery}`, { signal: controller.signal }),
      api<Metrics>(metricsPath, { signal: controller.signal }),
    ]).then(([foundScans, foundCodebases, foundMetrics]) => {
      setScans(foundScans); setCodebases(foundCodebases); setMetrics(foundMetrics);
      setHasMore(foundScans.length === 50);
    }).catch(exception => { if (!controller.signal.aborted) setError(exception.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); moreRequest.current?.abort(); };
  }, [programmer, projectLead, scopeId, filterQuery, refresh]);

  async function logout() {
    try { await api("/auth/logout", { method: "POST" }); onSignedOut(); }
    catch (exception) { setError(exception instanceof Error ? exception.message : "Unable to sign out"); }
  }

  async function loadMore() {
    moreRequest.current?.abort();
    const controller = new AbortController();
    moreRequest.current = controller;
    setMoreLoading(true);
    try {
      const records = await api<Scan[]>(`/scans?limit=50&offset=${scans.length}&${filterQuery}`, { signal: controller.signal });
      setScans(previous => [...previous, ...records.filter(record => !previous.some(scan => scan.scan_id === record.scan_id))]);
      setHasMore(records.length === 50);
    } catch (exception) { if (!controller.signal.aborted) setError(exception instanceof Error ? exception.message : "Unable to load scans"); }
    finally { if (!controller.signal.aborted) setMoreLoading(false); }
  }

  function navigate(destination: string) {
    setView(destination); setSelected(null); setSearch(""); setError(""); setNotice("");
  }
  function newScan(codebaseId = "") {
    setUploadBase(codebaseId); setUpload(true); setError("");
  }

  const navigation = [...(programmer ? ["Memberships"] : projectLead ? [setupView] : [setupView, "Project access"]), "Scans", "Codebases", ...(!programmer ? ["Results"] : []), "Scoring"];
  const nameOf = (id: string) => codebases.find(codebase => codebase.codebase_id === id)?.name || "Codebase";
  const selectedScore = programmer ? metrics.latest_score : projectLead ? metrics.average_project_score : metrics.average_documentation_score;
  const visibleScans = scans.filter(scan => nameOf(scan.codebase_id).toLowerCase().includes(search.toLowerCase()));
  const hasAssignment = programmer || !!scopeId;

  return <div className="app-shell">
    <header className="app-header">
      <a href="/" className="wordmark" onClick={event => { event.preventDefault(); navigate(programmer ? "Scans" : setupView); }}>IntelliDoc</a>
      <div className="account"><div><strong>{user.name}</strong><span>{user.role}</span></div>
        <button className="icon-button" aria-label="Sign out" onClick={logout}><LogOut size={18} /></button></div>
    </header>
    <nav className="main-nav" aria-label="Main navigation">{navigation.map(item => <button key={item}
      aria-current={!selected && view === item ? "page" : undefined} onClick={() => navigate(item)}>{item}</button>)}</nav>
    <main className="workspace-content">
      {error && <div className="error" role="alert">{error}</div>}
      {notice && <div className="notice" role="status">{notice}</div>}
      {selected ? <ScanResults key={selected.scan_id} scan={selected} codebase={codebases.find(codebase => codebase.codebase_id === selected.codebase_id)}
        canWrite={programmer} onBack={() => setSelected(null)} /> : <>
        <div className="page-heading"><div><h1>{view === "Scans" ? "Scan history" : view}</h1>
          <p>{view === setupView ? (projectLead ? "Create projects and share their IDs with your Team Leads." : "Create teams within existing projects. Share the team and project IDs with your programmers.")
            : view === "Scans" ? "Open a submission to review its source, findings and documentation score."
            : view === "Codebases" ? "Each codebase keeps its selected project and team across scans."
            : view === "Results" ? "Review team and programmer documentation results within the selected assignment."
            : view === "Memberships" ? "Request access by project/team name or ID. Once approved, open Scans to upload."
            : view === "Project access" ? "Request permission from the Project Lead before creating teams." : "How documentation scores are calculated."}</p></div>
          {programmer && ["Scans","Codebases"].includes(view) && <button className="primary" onClick={() => newScan()}><Plus size={17} />New scan</button>}
        </div>
        {!programmer && view !== setupView && view !== "Scoring" && view !== "Project access" && <div className="scope-bar"><label>{projectLead ? "Project" : "Team"}
          <select aria-label={`Review ${projectLead ? "project" : "team"}`} value={scopeId} onChange={event => { setScopeId(event.target.value); setSearch(""); }} disabled={organizationLoading}>
            {!scopeId && <option value="">{organizationLoading ? "Loading…" : `Create a ${projectLead ? "project" : "team"} first`}</option>}
            {projectLead ? projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name}</option>)
              : teams.map(team => <option key={team.team_id} value={team.team_id}>{team.team_name} · {team.project_name || "Legacy assignment"}</option>)}
          </select></label><button className="icon-button" onClick={reload} aria-label="Refresh results" disabled={loading}><RefreshCw size={17} /></button></div>}
        {!programmer && view === setupView ? <><Organization user={user} projects={projects} teams={teams} onRefresh={reload}
          onInspect={id => { setScopeId(id); navigate("Results"); }} />
          <MembershipAccess user={user} mode={projectLead?"project-approvals":"team-approvals"} refresh={refresh} onRefresh={reload}/>
          {projectLead&&<MembershipAccess user={user} mode="project-roster" refresh={refresh} onRefresh={reload}/>}</>
          : view === "Memberships" || view === "Project access" ? <MembershipAccess user={user} mode={programmer?"team-request":"project-request"} refresh={refresh} onRefresh={reload}/>
          : view === "Scoring" ? <ScoringGuide />
          : !hasAssignment ? <div className="empty"><h2>{projectLead ? "Create a project to begin" : "Create a team to begin"}</h2>
            <p>{projectLead ? "Your teams and their submissions will be grouped under the project." : "Your programmers will select your team when they upload code."}</p>
            <button onClick={() => navigate(setupView)}>Open {setupView.toLowerCase()}</button></div>
          : <>
            {loading && <p role="status" className="loading">Loading submissions…</p>}
            {view === "Codebases" ? <div className="table-scroll"><table><thead><tr><th>Codebase</th><th>Project</th><th>Team</th><th>Actions</th></tr></thead>
              <tbody>{codebases.map(codebase => {
                const latest = scans.find(scan => scan.codebase_id === codebase.codebase_id);
                return <tr key={codebase.codebase_id}><td className="strong">{codebase.name}</td><td>{codebase.project_name || "Unassigned"}</td>
                  <td>{codebase.team_name || "Legacy assignment"}</td><td className="row-actions">
                    {latest && <button className="link-button" onClick={() => setSelected(latest)}>Latest scan</button>}
                    {programmer && <button className="link-button" onClick={() => newScan(codebase.codebase_id)}>Rescan</button>}
                  </td></tr>;
              })}</tbody></table>{!loading && !codebases.length && <p className="empty">No codebases yet.</p>}</div> : <>
              <div className="result-summary"><span>{programmer ? "Latest score" : "Function-weighted score"} <strong>{scoreText(selectedScore)}<small> / 100</small></strong></span>
                <span>{codebases.length} codebases</span><span>{scans.length}{hasMore ? "+" : ""} scans loaded</span></div>
              {view === "Results" && <section className="table-section"><h2>{projectLead ? "Teams" : "Programmers"}</h2>
                <div className="table-scroll"><table><thead><tr><th>{projectLead ? "Team" : "Programmer"}</th><th>Functions</th><th>Documentation score</th></tr></thead><tbody>
                  {((projectLead?metrics.ranked_teams:metrics.ranked_programmers) || []).map((row, index) => <tr key={row.email || row.team_name || index}>
                    <td className="strong">{row.name || row.team_name}</td><td>{row.functions_count}</td><td>{scoreText(row.latest_score === undefined ? row.average_score : row.latest_score)}</td>
                  </tr>)}
                </tbody></table></div>
                {!((projectLead?metrics.ranked_teams:metrics.ranked_programmers) || []).length && <p className="empty">Results will appear when programmers join or submit to this assignment.</p>}
              </section>}
              {view === "Results" && projectLead && <section className="table-section"><h2>Programmers across this project</h2>
                <div className="table-scroll"><table><thead><tr><th>Programmer</th><th>Teams</th><th>Functions</th><th>Documentation score</th></tr></thead><tbody>
                  {(metrics.ranked_programmers||[]).map((row,index)=><tr key={row.email||index}><td className="strong">{row.name}<small className="table-note">{row.email}</small></td>
                    <td>{row.teams?.map(team=>team.team_name).join(", ")||"—"}</td><td>{row.functions_count}</td><td>{scoreText(row.latest_score)}</td></tr>)}
                </tbody></table></div><p className="field-note">Approved programmers without scored submissions show N/A. Scores measure supported documentation checks.</p>
              </section>}
              <section className="table-section"><div className="table-tools"><h2>Submissions</h2>
                <label className="search-field"><span className="sr-only">Find codebase</span><input type="search" placeholder="Find codebase" value={search} onChange={event => setSearch(event.target.value)} /></label></div>
                <div className="table-scroll"><table><thead><tr><th>Codebase</th><th>Submitted</th><th>Status</th><th>Score</th><th>Findings</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>
                  {visibleScans.map(scan => <tr key={scan.scan_id}><td><button className="link-button strong" onClick={() => setSelected(scan)}>{nameOf(scan.codebase_id)}</button>
                    <small className="table-note mono">{scan.scan_id.slice(0, 8)}</small></td><td>{dateText(scan.timestamp)}</td><td><Status value={scan.status} /></td>
                    <td>{scoreText(scan.summary?.documentation_score)}</td><td>{scan.summary?.total_findings ?? "—"}</td>
                    <td><button className="link-button" onClick={() => setSelected(scan)}>Open</button></td></tr>)}
                </tbody></table></div>
                {!loading && !visibleScans.length && <p className="empty">{search ? "No matching submissions." : programmer
                  ? "No scans yet. Select a project and team through New scan to upload your source."
                  : "No submissions for this assignment yet. Share its ID with the people submitting code."}</p>}
                {hasMore && <div className="pagination"><button disabled={loading || moreLoading} onClick={loadMore}>{moreLoading ? "Loading…" : "Load older scans"}</button></div>}
              </section>
              {!!scans.length && <details className="trend-details"><summary>Recent scan scores</summary><Trend scans={scans} /></details>}
            </>}
          </>}
      </>}
    </main>
    <footer className="app-footer">IntelliDoc<span>Python functions and Google-style docstrings</span></footer>
    {upload && <UploadScan codebases={codebases} initialCodebase={uploadBase} onClose={() => { setUpload(false); reload(); }}
      onComplete={scan => { setUpload(false); setView("Scans"); setSelected(scan); setNotice("Scan saved."); reload(); }} />}
  </div>;
}

function Trend({ scans }: { scans: Scan[] }) {
  const values = scans.filter(scan => scan.summary?.documentation_score != null).slice(0, 10).reverse();
  if (!values.length) return <p className="empty">No numeric scores yet.</p>;
  const points = values.map((scan, index) => ({
    x: values.length === 1 ? 300 : 50 + index * 500 / (values.length - 1),
    y: 160 - (scan.summary?.documentation_score || 0) * 1.3,
    scan,
  }));
  return <div className="trend"><p className="field-note">Latest 10 scored scans in this view. Select the same codebase for like-for-like comparison.</p>
    <svg viewBox="0 0 600 200" role="img" aria-label={`Recent documentation scores: ${values.map(scan => scan.summary?.documentation_score).join(", ")}`}>
      {[0, 50, 100].map(value => <g key={value}><text x="8" y={165 - value * 1.3}>{value}</text><line x1="40" x2="570" y1={160 - value * 1.3} y2={160 - value * 1.3} /></g>)}
      {points.length > 1 && <polyline points={points.map(point => `${point.x},${point.y}`).join(" ")} />}
      {points.map(point => <circle key={point.scan.scan_id} cx={point.x} cy={point.y} r="4"><title>{dateText(point.scan.timestamp)} · {scoreText(point.scan.summary?.documentation_score)}</title></circle>)}
      <text x="40" y="190">Earlier</text><text x="520" y="190">Latest</text>
    </svg>
  </div>;
}
