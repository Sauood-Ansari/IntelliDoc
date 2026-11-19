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

  return <main className="sign-in-page">
    <a className="wordmark" href="/">IntelliDoc<span>Python documentation review</span></a>
    <section className="sign-in-form">
      <h1>{register ? "Create an account" : "Sign in"}</h1>
      <p>{register ? "Choose the role you will use in your project." : "Open your projects, teams and code reviews."}</p>
      {error && <div className="error" role="alert">{error}</div>}
      <form onSubmit={submit}>
        {register && <>
          <label>Full name<input required maxLength={100} autoComplete="name" value={name} onChange={event => setName(event.target.value)} disabled={busy} /></label>
          <label>Role<select aria-label="Role" required value={role} onChange={event => setRole(event.target.value as Role)} disabled={busy}>
            <option value="">Choose a role</option>
            <option>Programmer</option><option>Team Lead</option><option>Project Lead</option>
          </select></label>
          {role && <p className="field-note">{role === "Project Lead" ? "Create projects, approve Team Leads and review project-wide results." : role === "Team Lead" ? "Request Project Lead approval, then create teams and approve programmers." : "Request membership in one or more teams. Upload after Team Lead approval."}</p>}
        </>}
        <label>Email<input type="email" required autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} disabled={busy} /></label>
        <label>Password<input type="password" required minLength={register ? 10 : 1} maxLength={72}
          autoComplete={register ? "new-password" : "current-password"} value={password}
          onChange={event => setPassword(event.target.value)} disabled={busy} /></label>
        {register && <p className="field-note">Use at least 10 characters.</p>}
        <button className="primary full-width" disabled={busy}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
      </form>
      <button className="link-button auth-switch" disabled={busy} onClick={() => { setRegister(!register); setError(""); }}>
        {register ? "Already have an account? Sign in" : "Create an account"}
      </button>
    </section>
    <p className="sign-in-footer">Project Leads approve Team Leads. Team Leads approve programmers. Approved members submit their code.</p>
  </main>;
}
