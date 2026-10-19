import { useCallback, useEffect, useState } from "react";
import api from "../api.js";
import { Badge, CardSkeleton } from "../App.jsx";

export default function Supply({ date }) {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!date) return;
    setError("");
    setPlan(null);
    try {
      const r = await api.get("/api/supply-plan", { params: { date } });
      setPlan(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load supply plan.");
    }
  }, [date]);

  useEffect(() => { load(); }, [load]);
  const alerts = plan?.wards.filter((w) => w.alert) || [];

  return (
    <>
      {plan === null && !error ? (
        <div className="grid3"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      ) : plan && (
        <>
          {!!alerts.length && (
            <div className="alertbanner shortage">
              <b>⚠ Shortage alert</b>
              <span>{alerts.map((w) => `${w.ward_id} (${w.category})`).join(", ")} on {plan.date} — prioritized in allocation below.</span>
            </div>
          )}
          <div className="grid4">
            {plan.pools.map((p) => {
              const used = plan.wards.filter((w) => w.reservoir_id === p.reservoir_id)
                .reduce((s, w) => s + w.allocated_ml, 0);
              const pct = Math.min(100, (used / p.pool_ml) * 100);
              return (
                <div className="card stat" key={p.reservoir_id}>
                  <h2>{p.reservoir_id} pool</h2>
                  <div className="value">{p.pool_ml.toFixed(1)} <span className="muted">ML</span></div>
                  <div className="utilbar"><div style={{ width: `${pct}%` }} /></div>
                  <div className="meta">{used.toFixed(1)} ML allocated ({pct.toFixed(0)}%) · {(p.reserve_pct * 100).toFixed(0)}% reserve held</div>
                </div>
              );
            })}
            <div className="card stat">
              <h2>Total allocated</h2>
              <div className="value">{plan.total_allocated_ml.toFixed(1)} <span className="muted">ML</span></div>
              <div className="meta">{plan.date} · severity-weighted, never over-allocated</div>
            </div>
          </div>
          <div className="card">
            <h2>Ward allocations</h2>
            <p className="sub">Capped at forecast demand — unmet surplus stays stored in the reservoir.</p>
            <div className="row" style={{ marginBottom: 12 }}>
              <button className="primary" onClick={() => {
                const rows = [["date", "ward_id", "reservoir_id", "forecast_ml", "allocated_ml", "met_pct", "category", "alert"]];
                plan.wards.forEach((w) => rows.push([plan.date, w.ward_id, w.reservoir_id, w.forecast_ml.toFixed(2), w.allocated_ml.toFixed(2), ((w.allocated_ml / w.forecast_ml) * 100).toFixed(0), w.category, w.alert ? "yes" : "no"]));
                rows.push([]);
                rows.push(["pool_reservoir_id", "pool_ml", "pool_allocated_ml", "reserve_pct"]);
                plan.pools.forEach((p) => {
                  const used = plan.wards.filter((w) => w.reservoir_id === p.reservoir_id).reduce((s, w) => s + w.allocated_ml, 0);
                  rows.push([p.reservoir_id, p.pool_ml.toFixed(1), used.toFixed(1), p.reserve_pct]);
                });
                const csv = rows.map((r) => r.join(",")).join("\n");
                const a = document.createElement("a");
                a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                a.download = `supply-plan-${plan.date}.csv`;
                a.click();
                URL.revokeObjectURL(a.href);
              }}>Export CSV</button>
              <span className="muted">Ward allocations + pool summary, {plan.wards.length} wards</span>
            </div>
            <table className="data">
              <thead><tr><th>Ward</th><th>Reservoir</th><th>Forecast ML</th><th>Allocated ML</th><th>Met %</th><th>Stress</th><th>Alert</th></tr></thead>
              <tbody>
                {plan.wards.map((w) => (
                  <tr key={w.ward_id} className={w.alert ? "alert-row" : ""}>
                    <td>{w.ward_id}</td><td>{w.reservoir_id}</td>
                    <td>{w.forecast_ml.toFixed(2)}</td><td>{w.allocated_ml.toFixed(2)}</td>
                    <td>{((w.allocated_ml / w.forecast_ml) * 100).toFixed(0)}%</td>
                    <td><Badge category={w.category} /></td>
                    <td>{w.alert ? "⚠ Shortage alert" : "—"}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr><td colSpan={3}>Total ({plan.wards.length} wards)</td>
                <td>{plan.total_allocated_ml.toFixed(2)}</td><td colSpan={3}>{alerts.length} alert{alerts.length === 1 ? "" : "s"} · {plan.date}</td></tr></tfoot>
            </table>
          </div>
        </>
      )}
      {error && <div className="error">{error} <button className="primary" onClick={load}>Retry</button></div>}
    </>
  );
}
