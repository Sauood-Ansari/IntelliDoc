export type Role = "Programmer" | "Team Lead" | "Project Lead";
export type User = {user_id:string;name:string;email:string;role:Role};
export type Project = {project_id:string;project_name:string;project_lead_id:string};
export type Team = {team_id:string;team_name:string;team_lead_id:string|null;project_id:string|null;project_name:string|null};
export type Codebase = {codebase_id:string;name:string;project_id:string|null;team_id:string|null;project_name:string|null;team_name:string|null};
export type Summary = {total_files:number;parsed_files:number;failed_files:number;total_functions:number;documented_functions:number;undocumented_functions:number;total_findings:number;documentation_score:number|null;breakdown?:Record<string,number|string>;error?:string};
export type Scan = {scan_id:string;codebase_id:string;timestamp:string;status:string;summary:Summary|null};
export type Finding = {finding_id:string;function_id:string;type:string;severity:string;explanation:string};
export type Func = {function_id:string;name:string;qualified_name:string;signature:string;docstring:string|null;has_docstring:boolean;file_path:string;line_number:number;source_code:string;findings:Finding[]};
export type SourceFile = {file_id:string;path:string;parse_status:string;error_message:string|null};
export type Analysis = {analysis_id:string;provider:string;analysis_type:string;result:string;status:string;review_status:string;reviewed_text:string|null};
export type Ranking = {name?:string;team_name?:string;email?:string;latest_score?:number|null;average_score?:number|null;functions_count:number;programmers_count?:number;teams?:{team_id:string;team_name:string}[]};
export type AccessRequest = {request_id:string;project_id:string;project_name:string;team_lead_id:string;requester_name:string;requester_email:string;status:"Pending"|"Approved"|"Rejected";decision_note:string|null;requested_at:string};
export type Membership = {membership_id:string;team_id:string;team_name:string;project_id:string;project_name:string;programmer_id:string;requester_name:string;requester_email:string;status:"Pending"|"Approved"|"Rejected";decision_note:string|null;requested_at:string};
export type Metrics = {latest_score?:number|null;average_documentation_score?:number|null;average_project_score?:number|null;team_name?:string;project_name?:string;ranked_programmers?:Ranking[];ranked_teams?:Ranking[]};
export async function api<T>(path:string, init:RequestInit = {}): Promise<T> {
  const response = await fetch("/api"+path,{...init,headers:{...(init.body instanceof FormData ? {} : {"Content-Type":"application/json"}),...init.headers},cache:"no-store"});
  const data = await response.json();
  if(!response.ok) {
    if(response.status === 401 && !path.includes("login") && path !== "/auth/me") window.dispatchEvent(new Event("session-expired"));
    const message = typeof data.detail === "string" ? data.detail : Array.isArray(data.detail) ? data.detail.map((d:{msg:string})=>d.msg).join("; ") : "Request failed";
    throw new Error(message);
  }
  return data;
}

