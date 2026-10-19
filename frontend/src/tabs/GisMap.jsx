import { useCallback, useEffect, useState } from "react";
import { CircleMarker, GeoJSON, MapContainer, Popup, TileLayer } from "react-leaflet";
import api from "../api.js";
import { Badge, ChartSkeleton } from "../App.jsx";
import "leaflet/dist/leaflet.css";

const FILL = { Safe: "#2e9e5b", Moderate: "#c9a100", "High Stress": "#e07b00", Shortage: "#d64545" };

function style(feature) {
  const c = feature?.properties?.category;
  return { color: "#0b3d62", weight: 2, fillColor: FILL[c] || "#999", fillOpacity: 0.55 };
}

export default function GisMap({ date }) {
  const [geo, setGeo] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!date) return;
    setError("");
    setGeo(null);
    try {
      const r = await api.get("/api/gis", { params: { date } });
      setGeo(r.data.wards);
      setMarkers(r.data.reservoirs);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load GIS layers.");
    }
  }, [date]);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      {error && <div className="error">{error} <button className="primary" onClick={load}>Retry</button></div>}
      {geo === null && !error ? <ChartSkeleton /> : geo && (
        <div className="card">
          <h2>Stress zones and reservoirs — {date}</h2>
          <p className="sub">Polygons are approximate centroid boxes (bmc-mumbai-approximate-centroid) — authoritative BMC boundaries pending. Tiles © OpenStreetMap contributors.</p>
          <MapContainer center={[19.08, 72.88]} zoom={11} style={{ height: 480, borderRadius: 12 }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <GeoJSON key={date} data={geo} style={style} />
            {markers.map((m) => (
              <CircleMarker key={m.reservoir_id} center={[m.lat, m.lon]} radius={10}
                pathOptions={{ color: "#0b3d62", fillColor: "#22b8cf", fillOpacity: 0.9 }}>
                <Popup>
                  <b>{m.name} ({m.reservoir_id})</b><br />
                  Storage: {m.storage_pct?.toFixed(1)}%<br />
                  Available: {m.available_ml?.toFixed(2)} ML
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
          <div className="row" style={{ marginTop: 12 }}>
            {Object.entries(FILL).map(([k, v]) => (
              <span key={k} className="muted"><span style={{ display: "inline-block", width: 12, height: 12, background: v, borderRadius: 3, marginRight: 4 }} />{k}</span>
            ))}
          </div>
          <div className="catkey" aria-label="Stress category key">
            <span className="muted">Category key:</span>
            <span><Badge category="Safe" /><span className="range">WAR ≥ 1.00</span></span>
            <span><Badge category="Moderate" /><span className="range">0.85 – 1.00</span></span>
            <span><Badge category="High Stress" /><span className="range">0.70 – 0.85</span></span>
            <span><Badge category="Shortage" /><span className="range">&lt; 0.70</span></span>
            <span className="muted">Live wards currently all Safe — key shows the full operational scale.</span>
          </div>
          <table className="data" style={{ marginTop: 12 }}>
            <thead><tr><th>Ward</th><th>Forecast ML</th><th>WAR</th><th>Status</th></tr></thead>
            <tbody>
              {geo.features.map((f) => (
                <tr key={f.properties.ward_id}>
                  <td>{f.properties.ward_id} — {f.properties.name}</td>
                  <td>{f.properties.forecast_ml.toFixed(2)}</td>
                  <td>{f.properties.war.toFixed(3)}</td>
                  <td>{f.properties.category}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
