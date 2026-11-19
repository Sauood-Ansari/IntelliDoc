"use client";

import { useEffect, useState } from "react";
import { Copy, Check } from "lucide-react";
import { api, Project, Team, User } from "@/lib/api";

type Option = { id: string; name: string };

export function DirectorySelect({ kind, value, onChange, projectId = "", disabled = false, eligible = false }: {
  kind: "projects" | "teams";
  value: string;
  onChange: (id: string) => void;
  projectId?: string;
  disabled?: boolean;
  eligible?: boolean;
}) {
  const [search, setSearch] = useState("");
  const [options, setOptions] = useState<Option[]>([]);
  const [selected, setSelected] = useState<Option | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const singular = kind === "projects" ? "project" : "team";
  const unavailable = disabled || (kind === "teams" && !projectId);

  function option(record: Project | Team): Option {
    if ("team_id" in record) return { id: record.team_id, name: record.team_name };
    return { id: record.project_id, name: record.project_name };
  }

  useEffect(() => { setSearch(""); setOptions([]); }, [projectId]);

  useEffect(() => {
    if (!value) { setSelected(null); return; }
    const controller = new AbortController();
    api<Project | Team>(`/${kind}/${value}`, { signal: controller.signal }).then(record => setSelected(option(record)))
      .catch(exception => { if (!controller.signal.aborted) setError(exception.message); });
    return () => controller.abort();
  }, [kind, value]);

  useEffect(() => {
    const controller = new AbortController();
    if (kind === "teams" && !projectId) { setOptions([]); return; }
    setLoading(true);
    const timer = setTimeout(() => {
      const query = new URLSearchParams({ search, limit: "100" });
      if (eligible) query.set("eligible", "true");
      if (kind === "teams") query.set("project_id", projectId);
      api<(Project | Team)[]>(`/${kind}?${query}`, { signal: controller.signal }).then(records => {
        setOptions(records.map(option));
        setError("");
      }).catch(exception => { if (!controller.signal.aborted) setError(exception.message); })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 200);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [kind, projectId, search, eligible]);

  const choices = selected && !options.some(item => item.id === selected.id) ? [selected, ...options] : options;
  return <fieldset className="directory-field" disabled={unavailable}>
    <legend>{kind === "projects" ? "Project" : "Team"}</legend>
    {!disabled && <input aria-label={`Find ${singular} by name or ID`} placeholder={`Find ${singular} by name or ID`}
      value={search} onChange={event => setSearch(event.target.value)} />}
    <select aria-label={`Choose ${singular}`} required value={value} onChange={event => onChange(event.target.value)}>
      <option value="">{loading ? "Loading…" : `Choose a ${singular}`}</option>
      {choices.map(item => <option key={item.id} value={item.id}>{item.name} · {item.id}</option>)}
    </select>
    {value && <span className="field-note mono">{value}</span>}
    {error && <span className="field-error" role="alert">{error}</span>}
    {!loading && !error && !choices.length && !unavailable && <span className="field-note">
      {search ? "No matches. Check the name or paste the complete ID." : eligible ? "No approved choices yet. Request access and wait for the responsible lead to approve it." : kind === "projects"
        ? "A Project Lead needs to create a project first."
        : "A Team Lead needs to create a team in this project first."}
    </span>}
  </fieldset>;
}

export function CopyId({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(timer);
  }, [copied]);
  return <span className="copy-id"><code>{value}</code><button className="icon-button" aria-label={`Copy ID ${value}`} onClick={async () => {
    try { await navigator.clipboard.writeText(value); setCopied(true); setError(""); }
    catch { setError("Select the ID and copy it manually."); }
  }}>{copied ? <Check size={14} /> : <Copy size={14} />}</button>{error && <span role="status">{error}</span>}</span>;
}

export function Organization({ user, projects, teams, onRefresh, onInspect }: {
  user: User;
  projects: Project[];
  teams: Team[];
  onRefresh: () => void;
  onInspect: (id: string) => void;
}) {
  const isProjectLead = user.role === "Project Lead";
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState("");

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setError(""); setCreated("");
    try {
      if (isProjectLead) {
        const record = await api<Project>("/projects", { method: "POST", body: JSON.stringify({ project_name: name }) });
        setCreated(`Project “${record.project_name}” created. Share its ID with your Team Lead.`);
      } else {
        const record = await api<Team>("/teams", { method: "POST", body: JSON.stringify({ team_name: name, project_id: projectId }) });
        setCreated(`Team “${record.team_name}” created. Programmers can now select it when uploading.`);
      }
      setName(""); onRefresh();
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to save");
    } finally { setBusy(false); }
  }

  return <>
    <section className="setup-section">
      <div><h2>Create a {isProjectLead ? "project" : "team"}</h2><p>{isProjectLead
        ? "Give your project a unique name. Its ID is generated when you save."
        : "After Project Lead approval, select the project and choose a unique team name. Request permission in Project access."}</p></div>
      <form onSubmit={create} className="setup-form">
        {!isProjectLead && <DirectorySelect kind="projects" value={projectId} onChange={setProjectId} disabled={busy} eligible />}
        <label>{isProjectLead ? "Project name" : "Team name"}<input required maxLength={isProjectLead ? 150 : 100}
          value={name} onChange={event => setName(event.target.value)} disabled={busy} /></label>
        {error && <div className="error" role="alert">{error}</div>}
        {created && <div className="notice" role="status">{created}</div>}
        <button className="primary" disabled={busy || !name.trim() || (!isProjectLead && !projectId)}>{busy ? "Saving…" : isProjectLead ? "Create project" : "Create team"}</button>
      </form>
    </section>
    <section className="table-section">
      <h2>Your {isProjectLead ? "projects" : "teams"}</h2>
      <div className="table-scroll"><table>
        <thead><tr><th>Name</th><th>{isProjectLead ? "Project ID" : "Team ID"}</th>{!isProjectLead && <th>Project</th>}<th><span className="sr-only">Actions</span></th></tr></thead>
        <tbody>{isProjectLead ? projects.map(project => <tr key={project.project_id}>
          <td className="strong">{project.project_name}</td><td><CopyId value={project.project_id} /></td>
          <td><button className="link-button" onClick={() => onInspect(project.project_id)}>View results</button></td>
        </tr>) : teams.map(team => <tr key={team.team_id}>
          <td className="strong">{team.team_name}</td><td><CopyId value={team.team_id} /></td><td>{team.project_name || "Legacy team without a project"}</td>
          <td><button className="link-button" onClick={() => onInspect(team.team_id)}>View results</button></td>
        </tr>)}</tbody>
      </table></div>
      {!(isProjectLead ? projects.length : teams.length) && <p className="empty">{isProjectLead ? "Create your first project above." : "Your teams will appear here after you create one."}</p>}
    </section>
  </>;
}
