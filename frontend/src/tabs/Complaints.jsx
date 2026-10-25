import { useCallback, useEffect, useState } from "react";
import api from "../api.js";
import { CardSkeleton, StatusPill } from "../App.jsx";

const TYPES = ["no-supply", "low-pressure", "leakage", "quality", "billing"];

function Modal({ title, onClose, children }) {
  return (
    <div className="modal-veil" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="ghost" onClick={onClose} aria-label="Close details">✕ Close</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Detail({ c, wards, onClose }) {
  const [photo, setPhoto] = useState(null);
  const [photoErr, setPhotoErr] = useState("");
  useEffect(() => {
    let url = null;
    api.get(`/api/complaints/${c.id}/photo`, { responseType: "blob" })
      .then((r) => { url = URL.createObjectURL(r.data); setPhoto(url); })
      .catch(() => setPhotoErr("Photo unavailable."));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [c.id]);
  const wname = wards.find((w) => w.ward_id === c.ward_id)?.name || c.ward_id;
  return (
    <Modal title={`Complaint #${c.id}`} onClose={onClose}>
      <dl className="detail-grid">
        <dt>Reporter</dt><dd>{c.reporter_name ?? <span className="muted">Citizen account #{c.user_id}</span>}</dd>
        <dt>Ward</dt><dd>{c.ward_id} — {wname}</dd>
        <dt>Type</dt><dd>{c.type}</dd>
        <dt>Status</dt><dd><StatusPill status={c.status} /></dd>
        <dt>Filed</dt><dd>{new Date(c.created_at).toLocaleString()}</dd>
        <dt>Address</dt><dd>{c.address || <span className="muted">—</span>}</dd>
        <dt>Description</dt><dd>{c.description || <span className="muted">—</span>}</dd>
        <dt>Incident photo</dt>
        <dd>{photo
          ? <img className="photo" src={photo} alt={`Incident photo for complaint #${c.id}`} />
          : photoErr || (c.has_photo ? "Loading…" : "No photo on file.")}</dd>
      </dl>
    </Modal>
  );
}

export default function Complaints({ user, wards, ward }) {
  const [list, setList] = useState(null);
  const [cward, setCward] = useState(ward || user.ward_id || "");
  const [type, setType] = useState("low-pressure");
  const [error, setError] = useState("");
  const [view, setView] = useState("all"); // admin ward viewing filter
  const [open, setOpen] = useState(null);

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
      {open && <Detail c={open} wards={wards} onClose={() => setOpen(null)} />}
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
          <div className="row" style={{ justifyContent: "space-between", alignItems: "end" }}>
            <h2 style={{ margin: 0 }}>
              {user.role === "admin" ? "All complaints" : "My complaints"} ({view === "all" ? list.length : list.filter((c) => c.ward_id === view).length})
            </h2>
            {user.role === "admin" && (
              <div className="field" style={{ minWidth: 180 }}>
                <label>Filter by ward</label>
                <select value={view} onChange={(e) => setView(e.target.value)}>
                  <option value="all">All wards ({list.length})</option>
                  {wards.map((w) => <option key={w.ward_id} value={w.ward_id}>
                    {w.ward_id} — {w.name} ({list.filter((c) => c.ward_id === w.ward_id).length})
                  </option>)}
                </select>
              </div>
            )}
          </div>
          {(view === "all" ? list : list.filter((c) => c.ward_id === view)).length ? (
            <table className="data">
              <thead><tr><th>ID</th><th>Ward</th><th>Reported by</th><th>Type</th><th>Status</th><th>Filed</th><th>Photo</th><th>Action</th></tr></thead>
              <tbody>
                {(view === "all" ? list : list.filter((c) => c.ward_id === view)).map((c) => (
                  <tr key={c.id}>
                    <td>#{c.id}</td><td>{c.ward_id}</td>
                    <td>{c.reporter_name ?? <span className="muted">citizen #{c.user_id}</span>}</td>
                    <td>{c.type}</td><td><StatusPill status={c.status} /></td>
                    <td>{new Date(c.created_at).toLocaleString()}</td>
                    <td>{c.has_photo ? <span className="verchip">📎 photo</span> : <span className="muted">—</span>}</td>
                    <td>
                      <button className="ghost" onClick={() => setOpen(c)}>View</button>
                      {user.role === "admin" && c.status === "Filed" && <button className="primary" onClick={() => setStatus(c.id, "In-progress")}>Start work</button>}
                      {user.role === "admin" && c.status === "In-progress" && <button className="primary" onClick={() => setStatus(c.id, "Resolved")}>Resolve</button>}
                      {user.role === "admin" && c.status === "Resolved" && <span className="muted">Done</span>}
                    </td>
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
