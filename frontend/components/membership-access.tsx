"use client";
import { useEffect, useState } from "react";
import { api, User, AccessRequest, Membership } from "@/lib/api";
import { DirectorySelect } from "./organization";

export function MembershipAccess({ user, mode, refresh, onRefresh }: {
  user:User; mode:"project-request"|"project-approvals"|"team-request"|"team-approvals"|"project-roster";
  refresh:number; onRefresh:()=>void;
}) {
  const projectRequest = mode === "project-request" || mode === "project-approvals";
  const outgoing = mode === "project-request" || mode === "team-request";
  const readOnly = mode === "project-roster";
  const endpoint = projectRequest ? "/project-access-requests" : "/team-memberships";
  const [rows,setRows] = useState<(AccessRequest|Membership)[]>([]);
  const [projectId,setProjectId] = useState("");
  const [teamId,setTeamId] = useState("");
  const [busy,setBusy] = useState(false);
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState("");
  const [notice,setNotice] = useState("");
  const [decision,setDecision] = useState<{id:string;action:"Approve"|"Reject"}|null>(null);
  const [note,setNote] = useState("");

  useEffect(()=>{
    const controller=new AbortController(); setLoading(true);
    api<(AccessRequest|Membership)[]>(endpoint,{signal:controller.signal}).then(setRows)
      .catch(e=>{if(!controller.signal.aborted)setError(e.message);})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[endpoint,refresh]);

  async function submit(event:React.FormEvent) {
    event.preventDefault();setBusy(true);setError("");setNotice("");
    try {
      const result=await api<AccessRequest|Membership>(endpoint,{method:"POST",body:JSON.stringify(projectRequest?{project_id:projectId}:{team_id:teamId})});
      setNotice(result.status === "Approved" ? "You already have approved access." : result.status === "Pending" ? "Request saved. The responsible lead can now review it." : "Request saved.");
      onRefresh();
    }catch(e){setError(e instanceof Error?e.message:"Unable to request access");}finally{setBusy(false);}
  }
  async function decide(event:React.FormEvent) {
    event.preventDefault();if(!decision)return;
    setBusy(true);setError("");setNotice("");
    try {
      await api(endpoint+"/"+decision.id,{method:"PATCH",body:JSON.stringify({decision:decision.action,note:note.trim()||null})});
      setNotice(decision.action === "Approve" ? "Access approved." : "Request rejected.");setDecision(null);setNote("");onRefresh();
    }catch(e){setError(e instanceof Error?e.message:"Unable to save decision");}finally{setBusy(false);}
  }
  const title = mode === "project-request" ? "Request project access" : mode === "team-request" ? "Request team membership"
    : mode === "project-approvals" ? "Team Lead access requests" : readOnly ? "Project membership overview" : "Programmer membership requests";
  return <section className="approval-section">
    <div className="table-tools"><h2>{title}</h2><button onClick={onRefresh} disabled={loading||busy}>Refresh requests</button></div>
    <p>{outgoing ? projectRequest ? "Ask the Project Lead for permission to create teams in their project." : "Select a project and team. Its Team Lead must approve your membership before you can upload. You can join multiple teams and projects."
      : readOnly ? "Programmer memberships are approved by Team Leads. Project-wide documentation performance is available in Results."
      : projectRequest ? "Approve Team Leads only for projects you own. Approval lets them create teams in that project." : "Approve programmers for teams you lead. Approved members can upload to the selected team."}</p>
    {error&&<div className="error" role="alert">{error}</div>}{notice&&<div className="notice" role="status">{notice}</div>}
    {outgoing&&<form className="request-form stack-form" onSubmit={submit}>
      <DirectorySelect kind="projects" value={projectId} onChange={id=>{setProjectId(id);setTeamId("");}} disabled={busy}/>
      {!projectRequest&&<DirectorySelect kind="teams" projectId={projectId} value={teamId} onChange={setTeamId} disabled={busy}/>}
      <button className="primary" disabled={busy||!projectId||(!projectRequest&&!teamId)}>{busy?"Saving…":"Request access"}</button>
    </form>}
    {decision&&<form className="decision-form stack-form" onSubmit={decide}>
      <h3>{decision.action} access for {rows.find(row=>("request_id" in row?row.request_id:row.membership_id)===decision.id)?.requester_name}</h3>
      <label>Decision note (optional)<textarea rows={2} maxLength={500} value={note} onChange={e=>setNote(e.target.value)} disabled={busy}/></label>
      <div className="form-actions"><button type="button" onClick={()=>setDecision(null)} disabled={busy}>Cancel decision</button>
        <button className="primary" disabled={busy}>{busy?"Saving…":`Confirm ${decision.action.toLowerCase()}`}</button></div>
    </form>}
    {loading&&<p role="status">Loading requests…</p>}
    <div className="table-scroll"><table><thead><tr>{!outgoing&&<th>Person</th>}<th>Project{!projectRequest&&" / Team"}</th><th>Status</th><th>Decision note</th>{!outgoing&&!readOnly&&<th>Decision</th>}</tr></thead>
      <tbody>{rows.map(row=>{const id="request_id" in row?row.request_id:row.membership_id;return <tr key={id}>
        {!outgoing&&<td><strong>{row.requester_name}</strong><small className="table-note">{row.requester_email}</small></td>}
        <td>{row.project_name}{"team_name" in row&&<small className="table-note">{row.team_name}</small>}</td>
        <td>{row.status}</td><td>{row.decision_note||"—"}</td>
        {!outgoing&&!readOnly&&<td>{row.status==="Pending"?<div className="row-actions">
          <button disabled={busy} onClick={()=>{setDecision({id,action:"Approve"});setNote("");}}>Approve</button>
          <button disabled={busy} onClick={()=>{setDecision({id,action:"Reject"});setNote("");}}>Reject</button>
        </div>:"—"}</td>}</tr>;})}</tbody></table></div>
    {!loading&&!rows.length&&<p className="empty">{outgoing?"No access requests yet.":"No requests in your scope."}</p>}
  </section>;
}
