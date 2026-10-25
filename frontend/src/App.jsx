import { useEffect, useState } from "react";
import api from "./api.js";
import Landing from "./Landing.jsx";
import { LogoMark } from "./LogoMark.jsx";
import Complaints from "./tabs/Complaints.jsx";
import Forecasts from "./tabs/Forecasts.jsx";
import GisMap from "./tabs/GisMap.jsx";
import Leakage from "./tabs/Leakage.jsx";
import Reservoirs from "./tabs/Reservoirs.jsx";
import Stress from "./tabs/Stress.jsx";
import Supply from "./tabs/Supply.jsx";

const ADMIN_TABS = [
  ["forecast", "Forecasts"],
  ["stress", "Water Stress"],
  ["supply", "Supply Plan"],
  ["gis", "GIS Map"],
  ["leakage", "Leakage"],
  ["reservoirs", "Reservoirs"],
  ["complaints", "Complaints"],
];
const CITIZEN_TABS = [
  ["forecast", "Forecasts"],
  ["stress", "Water Stress"],
  ["supply", "My Supply"],
  ["complaints", "Complaints"],
];

/** Public display config from the API — no user-visible constants live here. */
export function useMeta() {
  const [meta, setMeta] = useState(null);
  useEffect(() => {
    api.get("/api/meta")
      .then((r) => setMeta(r.data))
      .catch(() => setMeta({ // graceful fallback so the app still boots
        model_version: null, ward_count: null, war: null,
        window: { min_date: null, max_date: new Date().toISOString().slice(0, 10) },
      }));
  }, []);
  return meta;
}

export function badgeClass(category) {
  if (category === "Safe") return "safe";
  if (category === "Moderate") return "moderate";
  if (category === "High Stress") return "high";
  return "shortage";
}

export function Badge({ category }) {
  return <span className={`badge ${badgeClass(category)}`}><span className="dot" />{category}</span>;
}

const SEV_CLASS = { critical: "shortage", high: "high", medium: "moderate", low: "safe" };

export function SevPill({ value }) {
  const cls = SEV_CLASS[String(value || "").toLowerCase()] || "moderate";
  return <span className={`badge ${cls}`}><span className="dot" />{value}</span>;
}

export function StatusPill({ status }) {
  const cls = status === "Resolved" ? "resolved" : status === "In-progress" ? "inprog" : "filed";
  return <span className={`pill ${cls}`}>{status}</span>;
}

export function useWards() {
  const [wards, setWards] = useState([]);
  useEffect(() => {
    api.get("/api/wards").then((r) => setWards(r.data)).catch(() => setWards([]));
  }, []);
  return wards;
}

export function Skeleton({ height = 18, width = "100%", style }) {
  return <div className="skel" style={{ height, width, ...style }} />;
}

export function CardSkeleton() {
  return (
    <div className="card" aria-busy="true" aria-label="Loading">
      <Skeleton height={16} width="40%" style={{ marginBottom: 12 }} />
      <Skeleton height={34} width="60%" style={{ marginBottom: 8 }} />
      <Skeleton height={13} width="80%" />
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="card" aria-busy="true" aria-label="Loading chart">
      <Skeleton height={16} width="35%" style={{ marginBottom: 12 }} />
      <Skeleton height={260} />
    </div>
  );
}

export { LogoMark };

export function GovBar() {
  const [online, setOnline] = useState(null);
  useEffect(() => {
    let live = true;
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 5000);
    fetch(`${api.defaults.baseURL}/openapi.json`, { signal: ctl.signal })
      .then((r) => { if (live) setOnline(r.ok); })
      .catch(() => { if (live) setOnline(false); })
      .finally(() => clearTimeout(t));
    return () => { live = false; clearTimeout(t); ctl.abort(); };
  }, []);
  return (
    <div className="govbar">
      <span className="govtag">Govt of Maharashtra</span>
      <span>Brihanmumbai Municipal Corporation (BMC) · Water Operations</span>
      <span className="spacer" />
      {online === null ? <span className="muted">Checking API…</span> : online ? (
        <span className="live"><i />API Online</span>
      ) : (
        <span className="error" style={{ margin: 0, padding: "2px 10px" }}>API Unreachable</span>
      )}
    </div>
  );
}

const TYPES = ["no-supply", "low-pressure", "leakage", "quality", "billing", "others"];

function GuestComplaint({ onBack }) {
  const [pubWards, setPubWards] = useState([]);
  const [ward, setWard] = useState("");
  const [name, setName] = useState("");
  const [addr, setAddr] = useState("");
  const [type, setType] = useState("no-supply");
  const [desc, setDesc] = useState("");
  const [photo, setPhoto] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [ref, setRef] = useState(null);
  useEffect(() => {
    api.get("/api/public/wards").then((r) => {
      setPubWards(r.data);
      if (r.data.length) setWard((w) => w || r.data[0].ward_id);
    }).catch(() => setError("Could not load the ward list — check that the API is running."));
  }, []);

  function validate() {
    if (name.trim().length < 2) return "Please enter your full name (min 2 characters).";
    if (!ward) return "Please select the incident ward.";
    if (addr.trim().length < 5) return "Please describe the incident address (min 5 characters).";
    if (!photo) return "An incident photo is required (JPEG, PNG or WEBP up to 5 MB).";
    if (photo && photo.size > 5 * 1024 * 1024) return "Photo is larger than 5 MB.";
    if (type === "others" && desc.trim().length < 25) {
      return "For type “Others”, please explain the incident in detail in the description (min 25 characters).";
    }
    if (desc.trim().length < 10) return "Please describe the incident (min 10 characters).";
    return "";
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    const v = validate();
    if (v) { setError(v); return; }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("ward_id", ward);
      fd.append("type", type);
      fd.append("reporter_name", name);
      fd.append("address", addr);
      fd.append("description", desc);
      fd.append("photo", photo);
      const r = await api.post("/api/complaints/public", fd);
      setRef(r.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed — please retry.");
    }
    setBusy(false);
  }

  if (ref) {
    return (
      <div className="guest-done">
        <h2>Complaint received ✓</h2>
        <p>Your reference number:</p>
        <div className="refchip">#{ref.id}</div>
        <p className="muted">Ward {ref.ward_id} · {ref.type} · filed {new Date(ref.created_at).toLocaleString()}.<br />
          Track progress by citing <b>#{ref.id}</b> at your ward office.</p>
        <button className="ghost" onClick={onBack}>Back to sign-in</button>
      </div>
    );
  }
  return (
    <form onSubmit={submit} noValidate>
      <div className="field"><label>Full name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name of the person reporting" /></div>
      <div className="field"><label>Incident ward</label>
        <select value={ward} onChange={(e) => setWard(e.target.value)}>
          {pubWards.map((w) => <option key={w.ward_id} value={w.ward_id}>{w.ward_id} — {w.name}</option>)}
        </select></div>
      <div className="field"><label>Incident address (required)</label>
        <textarea rows={2} value={addr} onChange={(e) => setAddr(e.target.value)} placeholder="Street, landmark, house/plot no. inside the selected ward" /></div>
      <div className="field"><label>Incident type</label>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select></div>
      {type === "others" && (
        <p className="hint">
          You selected <b>Others</b> — since the incident type isn’t in the list, describe exactly
          what happened in the description field below (e.g. “overflowing valve chamber near the
          school gate since Monday”).
        </p>
      )}
      <div className="field"><label>Incident photo (required · JPEG/PNG/WEBP ≤ 5 MB)</label>
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setPhoto(e.target.files?.[0] || null)} />
        {photo && <span className="muted"> {photo.name}</span>}</div>
      <div className="field"><label>Incident description (required)</label>
        <textarea rows={4} value={desc} onChange={(e) => setDesc(e.target.value)} placeholder={type === "others"
          ? "Describe the incident in detail — what happened, when it started, severity, what makes it different from the listed types…"
          : "What happened, when it started, severity, how many households are affected…"} /></div>
      {error && <div className="error">{error}</div>}
      <button className="primary" type="submit" disabled={busy}>{busy ? "Submitting…" : "Submit complaint →"}</button>
    </form>
  );
}

function Login({ onLogin, initialMode = "signin", onHome, meta }) {
  const [mode, setMode] = useState(initialMode);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [regWard, setRegWard] = useState("");
  const [pubWards, setPubWards] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { setMode(initialMode); }, [initialMode]);
  useEffect(() => {
    if (mode === "register" && !pubWards.length) {
      api.get("/api/public/wards").then((r) => {
        setPubWards(r.data);
        if (!regWard && r.data.length) setRegWard(r.data[0].ward_id);
      }).catch(() => setError("Could not load ward list — check that the API is running."));
    }
  }, [mode]);
  async function doLogin(user, pass) {
    const r = await api.post("/api/auth/login", { username: user, password: pass });
    localStorage.setItem("ws_token", r.data.access_token);
    const me = await api.get("/api/auth/me");
    onLogin(me.data);
  }
  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await doLogin(username, password);
    } catch {
      setError("Sign-in failed — check your credentials and that the API is running.");
    }
    setBusy(false);
  }
  async function register(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.post("/api/auth/register", { username, password, role: "citizen", ward_id: regWard });
      await doLogin(username, password);
    } catch (err) {
      const code = err.response?.status;
      setError(code === 409 ? "Username taken — pick another."
        : (err.response?.data?.detail || "Registration failed — check that the API is running."));
    }
    setBusy(false);
  }
  return (
    <div className="login-page">
      <GovBar />
      <div className="login-wrap">
      <div className="login-card">
        <div className="login-brand">
          <div className="wordmark">
            <LogoMark size={40} />
            <div>
              <h1>WaterSphere AI <span className="pilot">Pilot</span></h1>
              <div className="div">MCGM Water Operations Division</div>
            </div>
          </div>
          <h2>Ward-level demand forecasts and reservoir-aware supply planning{meta && meta.ward_count ? ` for ${meta.ward_count} BMC wards` : ""}.</h2>
          <p className="desc">Operational hydraulic intelligence across the city’s reservoir network with multi-horizon demand estimation.</p>
          <ul className="caplist">
            <li><span className="capicon">▤</span><div><b>1 / 3 / 7-day ward demand forecasts</b><span>{meta?.window?.min_date && meta?.window?.max_date ? `Calibrated on ${meta.window.min_date.slice(0, 4)}–${meta.window.max_date.slice(0, 4)} ward telemetry, served per-horizon.` : "Calibrated on recorded ward telemetry, served per-horizon."}</span></div></li>
            <li><span className="capicon">◉</span><div><b>Water-stress classification (WAR)</b><span>{meta?.war ? `Safe ≥ ${meta.war.safe} · Moderate ${meta.war.moderate}–${meta.war.safe} · High ${meta.war.high}–${meta.war.moderate} · Shortage < ${meta.war.high}.` : "Classified by the water-availability ratio."}</span></div></li>
            <li><span className="capicon">⬢</span><div><b>Zone-wise supply plans + alerts</b><span>Severity-weighted allocation from the municipality’s reservoir pools.</span></div></li>
          </ul>
          <div className="meta">{meta?.model_version && <span className="verchip">{meta.model_version}</span>}<span className="muted" style={{ color: "var(--ws-deep-ink)" }}>Official use only</span></div>
        </div>
        <div className="login-form">
          <h2>{mode === "signin" ? "Municipal sign-in"
            : mode === "register" ? "Citizen registration" : "Report a water issue — no account"}</h2>
          <p className="muted">{mode === "signin"
            ? "Use your water-board account to continue."
            : mode === "register"
              ? "Create a citizen account locked to your ward."
              : "Guest reports need no account — a photo is required and your report goes straight to the ward office."}</p>
          {error && <div className="error"><b>{mode === "signin" ? "Authentication notice" : mode === "register" ? "Registration notice" : "Submission notice"}</b><br />{error}</div>}
          {mode === "signin" ? (
          <>
          <form onSubmit={submit}>
            <div className="field"><label>Officer username / Citizen ID</label>
              <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" placeholder="Enter your username" /></div>
            <div className="field"><label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" placeholder="••••••••" /></div>
            <button className="primary" type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in →"}</button>
          </form>
          <div className="divider"><span>or</span></div>
          <button className="secondary" onClick={() => { setError(""); setMode("guest"); }}>
            Report a complaint without sign-in
          </button>
          </>
          ) : mode === "register" ? (
          <form onSubmit={register}>
            <div className="field"><label>Citizen ID</label>
              <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" placeholder="Choose a citizen ID" /></div>
            <div className="field"><label>Password (min 6 characters)</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" placeholder="••••••••" /></div>
            <div className="field"><label>Your ward (locked after registration)</label>
              <select value={regWard} onChange={(e) => setRegWard(e.target.value)}>
                {pubWards.map((w) => <option key={w.ward_id} value={w.ward_id}>{w.ward_id} — {w.name}</option>)}
              </select></div>
            <button className="primary" type="submit" disabled={busy}>{busy ? "Creating…" : "Create citizen account →"}</button>
          </form>
          ) : (
          <GuestComplaint onBack={() => { setError(""); setMode("signin"); }} />
          )}
          <p className="muted" style={{ marginTop: 12 }}>
            {mode === "signin" ? (
              <>
                New here? <a href="#register" onClick={(e) => { e.preventDefault(); setError(""); setMode("register"); }}>Create a citizen account</a>
                {onHome && <>{" · "}<a href="#home" onClick={(e) => { e.preventDefault(); setMode("signin"); onHome(); }}>Back to home</a></>}
              </>
            ) : (
              <>Have an account? <a href="#signin" onClick={(e) => { e.preventDefault(); setError(""); setMode("signin"); }}>Back to sign-in</a></>
            )}
          </p>
        </div>
      </div>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("landing"); // signed-out entry: landing → login
  const [presets, setPresets] = useState({ initialMode: "signin" });
  const [tab, setTab] = useState("forecast");
  const meta = useMeta();
  const wards = useWards();
  const [ward, setWard] = useState("");
  const [date, setDate] = useState("");

  useEffect(() => {
    if (localStorage.getItem("ws_token")) {
      api.get("/api/auth/me").then((r) => setUser(r.data)).catch(() => {});
    }
  }, []);
  useEffect(() => {
    if (user?.role === "citizen" && user.ward_id) setWard(user.ward_id);
    else if (!ward && wards.length) setWard(wards[0].ward_id);
  }, [user, wards]);
  useEffect(() => {
    if (!date && meta?.window?.max_date) setDate(meta.window.max_date);
  }, [meta]);

  function goToLogin(initialMode) {
    setPresets({ initialMode });
    setView("login");
  }

  if (!user) {
    return view === "landing"
      ? <Landing meta={meta}
          onSignIn={() => goToLogin("signin")}
          onGuest={() => goToLogin("guest")} />
      : <Login onLogin={setUser} initialMode={presets.initialMode}
          onHome={() => setView("landing")} meta={meta} />;
  }

  const tabs = user.role === "admin" ? ADMIN_TABS : CITIZEN_TABS;
  const Tab = { forecast: Forecasts, stress: Stress, supply: Supply, gis: GisMap, leakage: Leakage, reservoirs: Reservoirs, complaints: Complaints }[tab] || Forecasts;
  const ctx = { user, wards, ward, date };
  const war = meta?.war;
  const warText = war
    ? `Safe ≥ ${war.safe} · Moderate ${war.moderate}–${war.safe} · High ${war.high}–${war.moderate} · Shortage < ${war.high}`
    : "Water-availability ratio bands";

  return (
    <>
      <GovBar />
      <div className="topbar">
        <div className="brand"><LogoMark size={30} /><h1>WaterSphere AI</h1></div>
        <span className="tag">pilot</span>
        {meta?.model_version && <span className="verchip">{meta.model_version}</span>}
        <span className="spacer" />
        <span className="rolechip">{user.role === "admin"
          ? (meta?.ward_count ? `Admin · all ${meta.ward_count} wards` : "Admin")
          : `Citizen · ${user.ward_id}`}</span>
        <span className="who">{user.username}</span>
        <button className="ghost" onClick={() => { localStorage.removeItem("ws_token"); setUser(null); setView("landing"); }}>Sign out</button>
      </div>
      <div className="contextbar">
        {user.role === "admin" ? (
          <div className="field"><label>Ward</label>
            <select value={ward} onChange={(e) => setWard(e.target.value)}>
              {wards.map((w) => <option key={w.ward_id} value={w.ward_id}>{w.ward_id} — {w.name}</option>)}
            </select></div>
        ) : (
          <span className="ward-chip">{ward || user.ward_id}</span>
        )}
        <div className="field"><label>Date</label>
          <input type="date" value={date}
            {...(meta?.window?.min_date ? { min: meta.window.min_date } : {})}
            {...(meta?.window?.max_date ? { max: meta.window.max_date } : {})}
            onChange={(e) => setDate(e.target.value)} /></div>
        <span className="verchip" title={warText}>{meta?.model_version ? `${meta.model_version} · live API` : "live API"}</span>
      </div>
      <div className="nav" role="tablist">
        {tabs.map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? "active" : ""} onClick={() => setTab(k)}>{label}</button>
        ))}
      </div>
      <div className="page"><Tab key={`${tab}-${user.username}`} {...ctx} /></div>
    </>
  );
}
