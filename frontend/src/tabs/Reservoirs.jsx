import { useCallback, useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api.js";
import { ChartSkeleton } from "../App.jsx";

function shift(dateStr, days) {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function Reservoirs({ date }) {
  const [resList, setResList] = useState([]);
  const [res, setRes] = useState("");
  const [series, setSeries] = useState(null);
  const [info, setInfo] = useState(null);
  const [allRes, setAllRes] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/reservoir").then((r) => {
      const ids = (r.data || []).map((x) => x.reservoir_id);
      setResList(ids);
      setAllRes(r.data || []);
      if (!res && ids.length) setRes(ids[0]);
    }).catch(() => setResList([]));
  }, []);

  const load = useCallback(async () => {
    if (!date || !res) return;
    setError("");
    setSeries(null);
    try {
      const r = await api.get("/api/reservoir", {
        params: { reservoir_id: res, date_from: shift(date, -60), date_to: date },
      });
      const [first] = r.data;
      setInfo(first);
      setSeries(first.readings.map((x) => ({
        date: x.date.slice(5), storage: x.storage_pct, available: x.available_ml,
      })));
    } catch {
      setError("Failed to load reservoir readings.");
    }
  }, [res, date]);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      <div className="card">
        <h2>Reservoir availability</h2>
        <div className="row">
          <div className="field"><label>Reservoir</label>
            <select value={res} onChange={(e) => setRes(e.target.value)}>
              {resList.map((id) => <option key={id} value={id}>{id}</option>)}
            </select></div>
        </div>
        {info && <p className="muted">Capacity {info.capacity_mcm} MCM · serves {info.serving_wards} · 60 days to {date}</p>}
      </div>
      {error && <div className="error">{error} <button className="primary" onClick={load}>Retry</button></div>}
      {series !== null && !error && !!series.length && (() => {
        const last = series[series.length - 1];
        const stor = series.map((x) => x.storage);
        const avail = series.map((x) => x.available);
        return (
          <div className="kpis">
            <div className="kpi"><div className="label">Storage — {res}</div>
              <div className="value">{last.storage.toFixed(1)}<small>%</small></div>
              <div className="delta">60d low {Math.min(...stor).toFixed(1)}% · high {Math.max(...stor).toFixed(1)}%</div></div>
            <div className="kpi"><div className="label">Available — {res}</div>
              <div className="value">{last.available.toFixed(0)}<small>ML</small></div>
              <div className="delta">60d low {Math.min(...avail).toFixed(0)} · high {Math.max(...avail).toFixed(0)} ML</div></div>
            <div className="kpi"><div className="label">Serves</div>
              <div className="value" style={{ fontSize: 18 }}>{info?.serving_wards || "—"}</div>
              <div className="delta">{info ? `${info.capacity_mcm} MCM capacity` : ""} · 60 days to {date}</div></div>
          </div>
        );
      })()}
      {series === null && !error ? <ChartSkeleton /> : !!series?.length && (
        <div className="card">
          <h2>Storage % and available ML</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={series} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" minTickGap={24} />
              <YAxis yAxisId="l" domain={["auto", "auto"]} label={{ value: "%", angle: -90, position: "insideLeft" }} />
              <YAxis yAxisId="r" orientation="right" domain={["auto", "auto"]} label={{ value: "ML", angle: 90, position: "insideRight" }} />
              <Tooltip formatter={(v, name) => [name === "storage" ? `${Number(v).toFixed(1)}%` : `${Number(v).toFixed(2)} ML`, name]} />
              <Legend />
              <Line yAxisId="l" type="monotone" dataKey="storage" stroke="#147cb5" strokeWidth={2} dot={false} name="storage %" />
              <Line yAxisId="r" type="monotone" dataKey="available" stroke="#22b8cf" strokeWidth={2} dot={false} name="available ML" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      {series?.length === 0 && <div className="empty">No readings in this window.</div>}
      {!!allRes.length && (
        <div className="card">
          <h2>All sources — {date}</h2>
          <p className="sub">Capacity and stored reading counts per source (selected row highlighted).</p>
          <table className="data">
            <thead><tr><th>Reservoir</th><th>Capacity MCM</th><th>Serves</th><th>Readings</th></tr></thead>
            <tbody>
              {allRes.map((r) => (
                <tr key={r.reservoir_id} style={r.reservoir_id === res ? { background: "#f4f9fd" } : undefined}>
                  <td>{r.reservoir_id}</td><td>{r.capacity_mcm}</td>
                  <td>{r.serving_wards}</td><td>{(r.readings || []).length}</td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr><td>Total ({allRes.length} sources)</td>
              <td>{allRes.reduce((s, r) => s + Number(r.capacity_mcm || 0), 0).toFixed(1)}</td>
              <td colSpan={2} /></tr></tfoot>
          </table>
        </div>
      )}
    </>
  );
}
