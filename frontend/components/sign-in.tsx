"use client";

import { useState } from "react";
import { api, Role, User } from "@/lib/api";

export function SignIn({ onSignedIn }: { onSignedIn: (user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role | "">("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (register) {
        await api("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password, role }) });
      }
      const user = await api<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setPassword("");
      onSignedIn(user);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  async function quickLogin(demoEmail: string, demoPass: string) {
    setBusy(true);
    setError("");
    setEmail(demoEmail);
    setPassword(demoPass);
    try {
      const user = await api<User>("/auth/login", { method: "POST", body: JSON.stringify({ email: demoEmail, password: demoPass }) });
      setPassword("");
      onSignedIn(user);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  return <main className="sign-in-page">
    <a className="wordmark" href="/">IntelliDoc<span>Python documentation review</span></a>
    <section className="sign-in-form">
      <h1>{register ? "Create an account" : "Sign in"}</h1>
      <p>{register ? "Choose the role you will use in your project." : "Open your projects, teams and code reviews."}</p>
      {error && <div className="error" role="alert">{error}</div>}
      <form onSubmit={submit}>
        {register && <>
          <label>Full name<input required maxLength={100} autoComplete="name" value={name} onChange={event => setName(event.target.value)} disabled={busy} /></label>
          <label>Role
            <select aria-label="Role" required value={role} onChange={event => setRole(event.target.value as Role)} disabled={busy} style={{ fontWeight: 600, padding: "0.5rem" }}>
              <option value="">-- Select Your Role --</option>
              <option value="Programmer">Programmer (Submit code & review drift)</option>
              <option value="Team Lead">Team Lead (Manage teams & approve programmers)</option>
              <option value="Project Lead">Project Lead (Create projects & oversee quality)</option>
            </select>
          </label>
          {role && <p className="field-note">{role === "Project Lead" ? "Create projects, approve Team Leads and review project-wide results." : role === "Team Lead" ? "Request Project Lead approval, then create teams and approve programmers." : "Request membership in one or more teams. Upload after Team Lead approval."}</p>}
        </>}
        <label>Email<input type="email" required autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} disabled={busy} /></label>
        <label>Password<input type="password" required minLength={register ? 10 : 1} maxLength={72}
          autoComplete={register ? "new-password" : "current-password"} value={password}
          onChange={event => setPassword(event.target.value)} disabled={busy} /></label>
        {register && <p className="field-note">Use at least 10 characters.</p>}
        <button className="primary full-width" disabled={busy}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
      </form>

      {!register && (
        <div style={{ marginTop: "1.25rem", borderTop: "1px solid #e2e8f0", paddingTop: "1rem" }}>
          <p style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.6rem", fontWeight: 600, textAlign: "center" }}>
            Quick Demo Sign-In by Role:
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.4rem" }}>
            <button type="button" className="secondary" disabled={busy} onClick={() => quickLogin("sauood@intellidoc.edu", "ProgPass123!")} style={{ fontSize: "0.75rem", padding: "0.5rem 0.25rem", textAlign: "center" }} title="Sign in as Programmer">
              👨‍💻 Programmer
            </button>
            <button type="button" className="secondary" disabled={busy} onClick={() => quickLogin("teamlead@intellidoc.edu", "TeamPass123!")} style={{ fontSize: "0.75rem", padding: "0.5rem 0.25rem", textAlign: "center" }} title="Sign in as Team Lead">
              👥 Team Lead
            </button>
            <button type="button" className="secondary" disabled={busy} onClick={() => quickLogin("projectlead@intellidoc.edu", "LeadPass123!")} style={{ fontSize: "0.75rem", padding: "0.5rem 0.25rem", textAlign: "center" }} title="Sign in as Project Lead">
              👑 Project Lead
            </button>
          </div>
        </div>
      )}

      <button className="link-button auth-switch" disabled={busy} onClick={() => { setRegister(!register); setError(""); }}>
        {register ? "Already have an account? Sign in" : "Create an account (Choose Role)"}
      </button>
    </section>
    <p className="sign-in-footer">Project Leads approve Team Leads. Team Leads approve programmers. Approved members submit their code.</p>
  </main>;
}
