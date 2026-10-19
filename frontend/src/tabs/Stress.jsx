import { useCallback, useEffect, useState } from "react";
import api from "../api.js";
import { Badge, CardSkeleton } from "../App.jsx";

export default function Stress({ user, wards, ward, date }) {
  const [detail, setDetail] = useState(null);
  const [table, setTable] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!ward || !date) return;
    setError("");
    setDetail(null);
    setTable(null);
    try {
      const list = user.role === "admin" ? wards : wards.filter((w) => w.ward_id === ward);
      const rows = await Promise.all(
        list.map((w) => api.get("/api/water-stress", { params: { ward_id: w.ward_id, date } }))
      );
      const data = rows.map((x) => x.data);
      setTable(data);
      setDetail(data.find((r) => r.ward_id === ward) || data[0]);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load water stress.");
    }
  }, [user, wards, ward, date]);

  useEffect(() => { if (wards.length) load(); }, [load, wards.length]);
  const trouble = (table || []).filter((r) => r.category === "Shortage" || r.category === "High Stress");

  return (
    <>
      {!!trouble.length && (
        <div className={`alertbanner ${trouble.some((r) => r.category === "Shortage") ? "shortage" : "high"}`}>
          <b>⚠ {trouble.length} ward{trouble.length === 1 ? "" : "s"} stressed</b>
          <span>{trouble.map((r) => `${r.ward_id} (${r.category}, WAR ${r.war.toFixed(2)})`).join(", ")} on {date}.</span>
        </div>
      )}
      {detail === null && !error ? <CardSkeleton /> : detail && (
        <div className="card stat">
          <h2>{detail.ward_id} — {date}</h2>
          <Badge category={detail.category} />
          <div className="value">WAR {detail.war.toFixed(3)}</div>
          <div className="warscale" role="img" aria-label={`WAR ${detail.war.toFixed(3)}, ${detail.category}`}>
            <div className="needle" style={{ left: `calc(${Math.min(100, (detail.war / 2) * 100)}% - 1px)` }} />
          </div>
          <div className="warticks"><span>0</span><span>0.70 shortage</span><span>0.85</span><span>1.0 safe</span><span>2.0</span></div>
          <div className="meta">forecast {detail.forecast_ml.toFixed(2)} ML ({detail.forecast_model}) · available {detail.available_ml.toFixed(2)} ML · gap {detail.gap_ml >= 0 ? "+" : ""}{detail.gap_ml.toFixed(2)} ML</div>
          <div className="meta">WAR = available ÷ forecast · bands provisional, pending municipal calibration</div>
        </div>
      )}
      {error && <div className="error">{error} <button className="primary" onClick={load}>Retry</button></div>}
      {table === null && !error ? <CardSkeleton /> : !!table?.length && (
        <div className="card">
          <h2>{user.role === "admin" ? "All wards" : "Your ward"} — {date}</h2>
          <p className="sub">One request per ward, served by the live stress engine.</p>
          <table className="data">
            <thead><tr><th>Ward</th><th>Forecast ML</th><th>Avail ML</th><th>Gap ML</th><th>WAR</th><th>Status</th></tr></thead>
            <tbody>
              {table.map((r) => (
                <tr key={r.ward_id} className={r.category === "Shortage" || r.category === "High Stress" ? "alert-row" : ""}>
                  <td>{r.ward_id}</td><td>{r.forecast_ml.toFixed(2)}</td><td>{r.available_ml.toFixed(2)}</td>
                  <td>{r.gap_ml >= 0 ? "+" : ""}{r.gap_ml.toFixed(2)}</td><td>{r.war.toFixed(3)}</td>
                  <td><Badge category={r.category} /></td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr><td>⌀ {table.length} wards ({trouble.length} stressed)</td><td colSpan={3} />
              <td>{(table.reduce((s, r) => s + r.war, 0) / table.length).toFixed(3)}</td><td /></tr></tfoot>
          </table>
        </div>
      )}
    </>
  );
}
