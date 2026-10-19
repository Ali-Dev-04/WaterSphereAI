import { useCallback, useEffect, useState } from "react";
import api from "../api.js";
import { CardSkeleton, StatusPill } from "../App.jsx";

const TYPES = ["no-supply", "low-pressure", "leakage", "quality", "billing"];

export default function Complaints({ user, wards, ward }) {
  const [list, setList] = useState(null);
  const [cward, setCward] = useState(ward || user.ward_id || "");
  const [type, setType] = useState("low-pressure");
  const [error, setError] = useState("");

  useEffect(() => { if (ward) setCward(ward); }, [ward]);

  const refresh = useCallback(async () => {
    try {
      const r = await api.get("/api/complaints");
      setList(r.data);
    } catch {
      setError("Failed to load complaints.");
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function file(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/api/complaints", { ward_id: cward, type });
      refresh();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to file complaint.");
    }
  }

  async function setStatus(id, status) {
    setError("");
    try {
      await api.patch(`/api/complaints/${id}`, { status });
      refresh();
    } catch (err) {
      setError(err.response?.data?.detail || "Status update failed.");
    }
  }

  return (
    <>
      <div className="card">
        <h2>File a complaint</h2>
        <form onSubmit={file}>
          <div className="row">
            <div className="field"><label>Ward</label>
              {user.role === "admin" ? (
                <select value={cward} onChange={(e) => setCward(e.target.value)}>
                  {wards.map((w) => <option key={w.ward_id} value={w.ward_id}>{w.ward_id}</option>)}
                </select>
              ) : <input value={user.ward_id} disabled />}</div>
            <div className="field"><label>Type</label>
              <select value={type} onChange={(e) => setType(e.target.value)}>
                {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select></div>
            <button className="primary" type="submit">File complaint</button>
          </div>
        </form>
      </div>
      {error && <div className="error">{error}</div>}
      {list === null && !error ? <CardSkeleton /> : (
        <div className="card">
          <h2>{user.role === "admin" ? `All complaints (${list.length})` : "My complaints"}</h2>
          {list.length ? (
            <table className="data">
              <thead><tr><th>ID</th><th>Ward</th><th>Type</th><th>Status</th><th>Filed</th>{user.role === "admin" && <th>Action</th>}</tr></thead>
              <tbody>
                {list.map((c) => (
                  <tr key={c.id}>
                    <td>#{c.id}</td><td>{c.ward_id}</td><td>{c.type}</td><td><StatusPill status={c.status} /></td>
                    <td>{new Date(c.created_at).toLocaleString()}</td>
                    {user.role === "admin" && (
                      <td>
                        {c.status === "Filed" && <button className="primary" onClick={() => setStatus(c.id, "In-progress")}>Start work</button>}
                        {c.status === "In-progress" && <button className="primary" onClick={() => setStatus(c.id, "Resolved")}>Resolve</button>}
                        {c.status === "Resolved" && <span className="muted">Done</span>}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <div className="empty">No complaints yet — filed complaints will appear here.</div>}
        </div>
      )}
    </>
  );
}
