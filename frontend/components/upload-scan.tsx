"use client";

import { useState } from "react";
import { api, Codebase, Scan } from "@/lib/api";
import { Dialog } from "./dialog";
import { DirectorySelect } from "./organization";

export function UploadScan({ codebases, initialCodebase = "", onClose, onComplete }: {
  codebases: Codebase[];
  initialCodebase?: string;
  onClose: () => void;
  onComplete: (scan: Scan) => void;
}) {
  const initial = codebases.find(codebase => codebase.codebase_id === initialCodebase);
  const [codebaseId, setCodebaseId] = useState(initialCodebase);
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState(initial?.project_id || "");
  const [teamId, setTeamId] = useState(initial?.team_id || "");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState<Codebase | null>(null);
  const choices = created && !codebases.some(codebase => codebase.codebase_id === created.codebase_id)
    ? [...codebases, created] : codebases;
  const existing = choices.find(codebase => codebase.codebase_id === codebaseId);

  function chooseCodebase(value: string) {
    const codebase = choices.find(item => item.codebase_id === value);
    setCodebaseId(value);
    setProjectId(codebase?.project_id || "");
    setTeamId(codebase?.team_id || "");
    setError("");
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !projectId || !teamId) return;
    if (!file.name.toLowerCase().endsWith(".zip") || file.size > 10 * 1024 * 1024) {
      setError("Choose a ZIP archive no larger than 10 MB.");
      return;
    }
    setBusy(true); setError("");
    try {
      let id = codebaseId;
      if (!id) {
        const codebase = await api<Codebase>("/codebases", { method: "POST", body: JSON.stringify({
          name: name.trim(), project_id: projectId, team_id: teamId,
        }) });
        id = codebase.codebase_id;
        setCreated(codebase);
        setCodebaseId(id);
      }
      const form = new FormData();
      form.append("codebase_id", id);
      form.append("project_id", projectId);
      form.append("team_id", teamId);
      form.append("file", file);
      const scan = await api<Scan>("/scans", { method: "POST", body: form });
      onComplete(scan);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to scan the archive");
    } finally { setBusy(false); }
  }

  return <Dialog title="New scan" onClose={onClose} busy={busy}>
    <p>Select an approved project and team, then upload your Python source. Request team access in Memberships first if needed.</p>
    <form onSubmit={submit} className="stack-form">
      <label>Codebase<select value={codebaseId} onChange={event => chooseCodebase(event.target.value)} disabled={busy}>
        <option value="">Create a new codebase</option>
        {choices.map(codebase => <option key={codebase.codebase_id} value={codebase.codebase_id}>{codebase.name}</option>)}
      </select></label>
      {!codebaseId && <label>Codebase name<input required maxLength={150} value={name} onChange={event => setName(event.target.value)} disabled={busy} /></label>}
      <DirectorySelect kind="projects" value={projectId} disabled={busy || !!existing?.project_id} eligible
        onChange={id => { setProjectId(id); setTeamId(""); }} />
      <DirectorySelect kind="teams" projectId={projectId} value={teamId} onChange={setTeamId} eligible
        disabled={busy || !!existing?.team_id} />
      {existing && <p className="field-note">This codebase keeps its saved project and team. Create a new codebase to submit under a different assignment.</p>}
      <label>Python ZIP archive<input type="file" required accept=".zip,application/zip" disabled={busy}
        onChange={event => setFile(event.target.files?.[0] || null)} /></label>
      <p className="field-note">Up to 10 MB compressed. Source is parsed without execution. AI runs only when requested on a function.</p>
      {error && <div className="error" role="alert">{error}</div>}
      {busy && <p role="status">Scanning files and saving results. Keep this window open.</p>}
      <div className="form-actions"><button type="button" onClick={onClose} disabled={busy}>Cancel</button>
        <button className="primary" disabled={busy || !file || !projectId || !teamId || (!codebaseId && !name.trim())}>
          {busy ? "Scanning…" : "Run scan"}
        </button></div>
    </form>
  </Dialog>;
}
