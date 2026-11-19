"use client";

import { useEffect, useState } from "react";
import { ArrowDownToLine, ArrowLeft } from "lucide-react";
import { api, Analysis, Codebase, Func, Scan, SourceFile } from "@/lib/api";
import { Dialog } from "./dialog";

export const scoreText = (value: number | null | undefined) => value == null ? "N/A" : value.toFixed(2).replace(/\.?0+$/, "");
export const dateText = (value: string) => new Date(value.endsWith("Z") ? value : value + "Z")
  .toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

export function Status({ value }: { value: string }) {
  return <span className={`status status-${value.toLowerCase().replaceAll(" ", "-")}`}>{value}</span>;
}

function FunctionInspector({ func, canWrite, onClose }: { func: Func; canWrite: boolean; onClose: () => void }) {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    api<Analysis[]>(`/functions/${func.function_id}/analyses`, { signal: controller.signal }).then(records => {
      setAnalyses(records);
      const latest = records.filter(record => record.analysis_type === "Draft Generation" && record.status === "Completed").at(-1);
      if (latest) setDraft(latest.reviewed_text ?? latest.result);
    }).catch(exception => { if (!controller.signal.aborted) setError(exception.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [func.function_id]);

  async function requestAI() {
    setBusy(true); setError(""); setNotice("");
    try {
      const action = func.has_docstring ? "consistency-check" : "generate-doc";
      const record = await api<Analysis>(`/functions/${func.function_id}/${action}`, { method: "POST" });
      setAnalyses(previous => [...previous, record]);
      if (record.analysis_type === "Draft Generation" && record.status === "Completed") setDraft(record.result);
    } catch (exception) { setError(exception instanceof Error ? exception.message : "AI request failed"); }
    finally { setBusy(false); }
  }

  async function review(record: Analysis, decision: "Accepted" | "Rejected") {
    setBusy(true); setError("");
    try {
      const saved = await api<Analysis>(`/functions/${func.function_id}/analyses/${record.analysis_id}`, {
        method: "PATCH", body: JSON.stringify({ decision, edited_text: draft }),
      });
      setAnalyses(previous => previous.map(item => item.analysis_id === saved.analysis_id ? saved : item));
      setNotice("Review saved. Apply any accepted edits to your source, then rescan.");
    } catch (exception) { setError(exception instanceof Error ? exception.message : "Unable to save review"); }
    finally { setBusy(false); }
  }

  const latestDraft = analyses.filter(record => record.analysis_type === "Draft Generation" && record.status === "Completed").at(-1);
  return <Dialog title={func.qualified_name || func.name} onClose={onClose} busy={busy} wide>
    <p className="mono">{func.file_path}:{func.line_number}</p>
    <h3>Submitted source</h3><pre className="source-code">{func.source_code || func.signature}</pre>
    <h3>Findings</h3>
    {func.findings.length ? <ul className="findings-list">{func.findings.map(finding => <li key={finding.finding_id}>
      <div><strong>{finding.type}</strong><Status value={finding.severity} /></div><p>{finding.explanation}</p>
    </li>)}</ul> : <p>No structural findings from the supported checks.</p>}
    <section className="ai-section">
      <h3>AI review</h3>
      <p>The selected function is sent to Groq-hosted GPT-OSS 120B when you request assistance. Review its advice before using it. The scan score comes from the structural checks.</p>
      {error && <div className="error" role="alert">{error}</div>}
      {notice && <div className="notice" role="status">{notice}</div>}
      {canWrite && <button disabled={busy || loading} onClick={requestAI}>
        {busy ? "Please wait…" : func.has_docstring ? "Check logical consistency" : "Generate documentation draft"}
      </button>}
      {loading && <p role="status">Loading saved AI reviews…</p>}
      {analyses.map(record => <article className="analysis-record" key={record.analysis_id}>
        <header><strong>{record.analysis_type}</strong><Status value={record.status} /></header>
        <p className="field-note">{record.provider} · Review {record.review_status.toLowerCase()}</p>
        {record === latestDraft ? <>
          <label>Documentation draft<textarea rows={10} value={draft} readOnly={!canWrite} disabled={busy}
            onChange={event => setDraft(event.target.value)} /></label>
          {canWrite && <div className="form-actions">
            <button disabled={busy || !draft.trim()} onClick={() => review(record, "Accepted")}>Accept draft</button>
            <button disabled={busy} onClick={() => review(record, "Rejected")}>Reject</button>
            <button disabled={busy} onClick={async () => {
              try { await navigator.clipboard.writeText(draft); setNotice("Draft copied."); }
              catch { setNotice("Select and copy the draft text manually."); }
            }}>Copy text</button>
          </div>}
        </> : <pre className={`ai-output ${record.status === "Failed" ? "field-error" : ""}`}>{record.result}</pre>}
      </article>)}
    </section>
  </Dialog>;
}

export function ScanResults({ scan, codebase, canWrite, onBack }: {
  scan: Scan; codebase?: Codebase; canWrite: boolean; onBack: () => void;
}) {
  const [functions, setFunctions] = useState<Func[]>([]);
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("Functions");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All functions");
  const [active, setActive] = useState<Func | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      api<Func[]>(`/scans/${scan.scan_id}/functions`, { signal: controller.signal }),
      api<SourceFile[]>(`/scans/${scan.scan_id}/files`, { signal: controller.signal }),
    ]).then(([foundFunctions, foundFiles]) => { setFunctions(foundFunctions); setFiles(foundFiles); })
      .catch(exception => { if (!controller.signal.aborted) setError(exception.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [scan.scan_id]);

  function download() {
    const blob = new Blob([JSON.stringify({ scan, files, functions }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url; link.download = `intellidoc-${scan.scan_id}.json`; link.click();
    URL.revokeObjectURL(url);
  }

  const filtered = functions.filter(func => {
    const text = [func.qualified_name, func.file_path, ...func.findings.map(finding => finding.type)].join(" ").toLowerCase();
    const matchesFilter = filter === "All functions" || (filter === "With findings" && func.findings.length > 0)
      || (filter === "Undocumented" && !func.has_docstring) || (filter === "Clean" && !func.findings.length);
    return text.includes(search.toLowerCase()) && matchesFilter;
  });

  return <>
    <button className="link-button back-link" onClick={onBack}><ArrowLeft size={15} />All scans</button>
    <div className="page-heading"><div><h1>{codebase?.name || "Scan results"}</h1>
      <p>{dateText(scan.timestamp)} · <Status value={scan.status} /></p>
      {codebase && <p>{codebase.project_name || "Unassigned project"} / {codebase.team_name || "Legacy team assignment"}</p>}
    </div><button disabled={loading || !!error} onClick={download}><ArrowDownToLine size={16} />Export JSON</button></div>
    <dl className="scan-summary">
      <div><dt>Documentation score</dt><dd>{scoreText(scan.summary?.documentation_score)}<small> / 100</small></dd></div>
      <div><dt>Functions</dt><dd>{scan.summary?.total_functions ?? 0}</dd></div>
      <div><dt>Findings</dt><dd>{scan.summary?.total_findings ?? 0}</dd></div>
      <div><dt>Files with errors</dt><dd>{scan.summary?.failed_files ?? 0}</dd></div>
    </dl>
    {scan.summary?.error && <div className="error" role="alert">{scan.summary.error}</div>}
    {scan.status === "Partial" && <p className="notice">Some files could not be parsed. The score covers the extracted functions. Review file errors below.</p>}
    {error && <div className="error" role="alert">{error}</div>}
    <div className="section-tabs" role="tablist" aria-label="Scan details">
      {["Functions", "Files", "Score breakdown"].map(value => <button role="tab" key={value}
        aria-selected={tab === value} aria-controls="scan-tab-panel" id={`tab-${value.replaceAll(" ", "-")}`}
        onClick={() => setTab(value)}>{value}</button>)}
    </div>
    {loading ? <p role="status">Loading scan details…</p> : <section id="scan-tab-panel" role="tabpanel" aria-labelledby={`tab-${tab.replaceAll(" ", "-")}`}>
      {tab === "Functions" ? <>
        <div className="table-tools"><label className="search-field">Find function<input type="search" placeholder="Name, path or finding" value={search} onChange={event => setSearch(event.target.value)} /></label>
          <label>Show<select value={filter} onChange={event => setFilter(event.target.value)}>{["All functions", "With findings", "Undocumented", "Clean"].map(value => <option key={value}>{value}</option>)}</select></label></div>
        <div className="table-scroll"><table><thead><tr><th>Function / location</th><th>Docstring</th><th>Findings</th><th>Review</th></tr></thead><tbody>
          {filtered.map(func => <tr key={func.function_id}>
            <td><button className="link-button mono" onClick={() => setActive(func)}>{func.qualified_name || func.name}</button><small className="table-note mono">{func.file_path}:{func.line_number}</small></td>
            <td>{func.has_docstring ? "Present" : "Missing"}</td><td>{func.findings.length}</td>
            <td><button className="link-button" onClick={() => setActive(func)}>Inspect</button></td>
          </tr>)}
        </tbody></table></div>
        {!filtered.length && <p className="empty">{functions.length ? "No matching functions." : "No functions were extracted. Check file errors or upload source containing functions."}</p>}
      </> : tab === "Files" ? <ul className="file-list">{files.map(file => <li key={file.file_id}>
        <div><span className="mono">{file.path}</span><Status value={file.parse_status} /></div>
        {file.error_message && <p className="field-error">{file.error_message}</p>}
      </li>)}</ul> : <ScoringGuide breakdown={scan.summary?.breakdown} />}
    </section>}
    {active && <FunctionInspector key={active.function_id} func={active} canWrite={canWrite} onClose={() => setActive(null)} />}
  </>;
}

export function ScoringGuide({ breakdown }: { breakdown?: Record<string, number | string> }) {
  const components = [
    { title: "Completeness", maximum: 40, key: "completeness_score", description: "40 multiplied by the fraction of functions with a non-empty docstring." },
    { title: "Parameter consistency", maximum: 40, key: "parameter_consistency", description: "Starts at 40, subtracts parameter penalties and multiplies by the documented fraction." },
    { title: "Return / yield consistency", maximum: 20, key: "return_consistency", description: "Starts at 20, subtracts return/yield penalties and multiplies by the documented fraction." },
  ];
  return <div className="prose">
    <h2>Documentation Reliability Score</h2>
    <p>A score from 0 to 100 summarizes the supported documentation checks for a scan.</p>
    <dl className="score-components">{components.map(component => <div key={component.key}>
      <dt>{component.title}</dt><dd>{breakdown && typeof breakdown[component.key] === "number" ? scoreText(breakdown[component.key] as number) : component.maximum}<small> / {component.maximum}</small></dd>
      <p>{component.description}</p>
    </div>)}</dl>
    <h3>Penalties and coverage</h3>
    <p>High findings have a raw penalty of 4, Medium 2 and Low 1. Each consistency component is bounded at zero before coverage scaling. Missing docstrings reduce the documented fraction and do not receive a second penalty.</p>
    <p>For 100 functions with 80 documented, three Medium parameter findings and no return findings, the score is 32 + 27.2 + 16 = 75.2.</p>
    <p>Zero extracted functions gives N/A. AI advice does not enter the calculation. The 40/40/20 weights are an academic policy for structural documentation checks. They do not establish runtime correctness or general programmer ability.</p>
    <h3>Lead averages</h3>
    <p>Team and project results use function-weighted scores from the latest available Score per codebase in the selected assignment. Empty scans contribute no weight. Early failures without a Score may leave an earlier result as the latest available score.</p>
  </div>;
}
