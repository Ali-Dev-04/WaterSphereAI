import { useCallback, useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api.js";
import { CardSkeleton, ChartSkeleton } from "../App.jsx";

function shift(dateStr, days) {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function Forecasts({ ward, date }) {
  const [cards, setCards] = useState(null);
  const [series, setSeries] = useState(null);
  const [minfo, setMinfo] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!ward || !date) return;
    setError("");
    setCards(null);
    setSeries(null);
    try {
      const [fc0, fc1, fc2, mi] = await Promise.all([
        api.get("/api/forecast", { params: { ward_id: ward, target_date: date, horizon: "1d" } }),
        api.get("/api/forecast", { params: { ward_id: ward, target_date: date, horizon: "3d" } }),
        api.get("/api/forecast", { params: { ward_id: ward, target_date: date, horizon: "7d" } }),
        api.get("/api/model-info").catch(() => null),
      ]);
      const fc = [fc0, fc1, fc2];
      setCards(fc.map((r) => r.data));
      if (mi) setMinfo(mi.data);
      const hist = await api.get("/api/consumption", {
        params: { ward_id: ward, date_from: shift(date, -45), date_to: date },
      });
      setSeries(hist.data.map((r) => ({ date: r.date.slice(5), demand: r.demand_ml })));
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load forecasts.");
    }
  }, [ward, date]);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      <div className="grid3">
        {cards === null && !error ? (
          <><CardSkeleton /><CardSkeleton /><CardSkeleton /></>
        ) : cards?.map((c) => (
          <div className="card stat" key={c.horizon}>
            <h2>{c.horizon === "1d" ? "1-day" : c.horizon === "3d" ? "3-day" : "7-day"} demand</h2>
            <div className="value">{c.predicted_ml.toFixed(2)} <span className="muted">ML</span></div>
            <div className="meta">{c.model} · {minfo?.test_scores?.[c.horizon]
              ? `MAPE ${minfo.test_scores[c.horizon].mape.toFixed(1)}% · R² ${minfo.test_scores[c.horizon].r2.toFixed(3)} (test)`
              : "test scores loading…"}</div>
            <div className="meta">target {c.target_date} · {c.ward_id} · v{c.model_version}</div>
          </div>
        ))}
      </div>
      {error && <div className="error">{error} <button className="primary" onClick={load}>Retry</button></div>}
      {series === null && !error ? <ChartSkeleton /> : !!series?.length && (
        <div className="card">
          <h2>Actual demand — trailing 45 days</h2>
          <p className="sub">Dots mark the three horizon forecasts for {date}.</p>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={series} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" minTickGap={24} />
              <YAxis domain={["auto", "auto"]} label={{ value: "ML", angle: -90, position: "insideLeft" }} />
              <Tooltip formatter={(v) => [`${Number(v).toFixed(2)} ML`, "demand"]} />
              <Line type="monotone" dataKey="demand" stroke="#147cb5" strokeWidth={2} dot={false} name="actual" />
              <ReferenceLine x={date.slice(5)} stroke="#5b7288" strokeDasharray="4 4" label={{ value: "target", fontSize: 11 }} />
              {cards?.map((c) => (
                <ReferenceDot key={c.horizon} x={date.slice(5)} y={c.predicted_ml} r={7}
                  fill="#22b8cf" stroke="#0b3d62" />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <p className="muted">Legend: line = actual · dots = 1/3/7-day forecasts. Test accuracy per card · bmc-v1 validated{minfo ? ` (active: ${Object.entries(minfo.active_per_horizon).map(([h, m]) => `${h} ${m}`).join(", ")})` : ""}.</p>
        </div>
      )}
      {series?.length === 0 && <div className="empty">No consumption history for {ward} up to {date}.</div>}
    </>
  );
}
