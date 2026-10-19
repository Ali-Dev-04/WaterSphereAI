import { useCallback, useEffect, useState } from "react";
import api from "../api.js";
import { CardSkeleton, SevPill } from "../App.jsx";

function shift(dateStr, days) {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function Leakage({ wards, ward, date }) {
  const [report, setReport] = useState(null);
  const [maint, setMaint] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!ward || !date) return;
    setError("");
    setReport(null);
    try {
      const [r, m] = await Promise.all([
        api.get("/api/leakage-risk", { params: { ward_id: ward, date_from: shift(date, -49), date_to: date } }),
        api.get("/api/maintenance", { params: { ward_id: ward } }),
      ]);
      setReport(r.data);
      setMaint(m.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load leakage analysis.");
    }
  }, [ward, date]);

  useEffect(() => { if (wards.length) load(); }, [load, wards.length]);

  return (
    <>
      <div className="card">
        <h2>Leakage / wastage — {ward}</h2>
        <p className="sub">Trailing 50 days to {date} · unsupervised IsolationForest flags · supervised classification deferred until real labels exist.</p>
      </div>
      {error && <div className="error">{error} <button className="primary" onClick={load}>Retry</button></div>}
      {report === null && !error ? (
        <div className="grid3"><CardSkeleton /><CardSkeleton /></div>
      ) : report && (
        <>
          <div className="grid3">
            <div className="card stat"><h2>Total loss</h2>
              <div className="value">{report.loss_ml_total.toFixed(1)} <span className="muted">ML</span></div>
              <div className="meta">{report.loss_pct_avg.toFixed(1)}% of supplied · {report.readings} readings</div></div>
            <div className="card stat"><h2>Flagged days</h2>
              <div className="value">{report.flagged}</div>
              <div className="meta">{report.from} → {report.to}</div></div>
          </div>
          <div className="card">
            <h2>Anomaly flags</h2>
            {report.flags.length ? (
              <table className="data">
                <thead><tr><th>Date</th><th>Loss ML</th><th>Loss %</th><th>Score</th><th>Severity</th></tr></thead>
                <tbody>
                  {report.flags.map((f) => (
                    <tr key={f.date} className={f.severity === "high" ? "alert-row" : ""}>
                      <td>{f.date}</td><td>{f.loss_ml.toFixed(2)}</td><td>{f.loss_pct.toFixed(1)}</td>
                      <td>{f.score.toFixed(3)}</td><td><SevPill value={f.severity} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <div className="empty">No anomalies in this window — loss patterns look normal.</div>}
          </div>
          <div className="card">
            <h2>Maintenance incidents — {ward}</h2>
            {maint.length ? (
              <table className="data">
                <thead><tr><th>ID</th><th>Date</th><th>Type</th><th>Cause</th><th>Severity</th></tr></thead>
                <tbody>
                  {maint.map((m) => (
                    <tr key={m.incident_id}><td>{m.incident_id}</td><td>{m.date}</td>
                      <td>{m.type}</td><td>{m.cause}</td><td><SevPill value={m.severity} /></td></tr>
                  ))}
                </tbody>
              </table>
            ) : <div className="empty">No recorded incidents for this ward.</div>}
          </div>
        </>
      )}
    </>
  );
}
