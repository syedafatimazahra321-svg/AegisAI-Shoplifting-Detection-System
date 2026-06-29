import { useEffect, useState } from "react";

const API = "http://localhost:8000";

function IncidentTable({ onSelect, selectedId }) {
  const [incidents, setIncidents] = useState([]);

  const fetchIncidents = () => {
    fetch(`${API}/api/incidents?limit=50`)
      .then((r) => r.json())
      .then(setIncidents)
      .catch(() => {});
  };

  useEffect(() => {
    fetchIncidents();
    const id = setInterval(fetchIncidents, 10000);
    return () => clearInterval(id);
  }, []);

  const statusLabel = {
    confirmed:   "CONFIRMED",
    pending:     "PENDING",
    "false-alarm": "FALSE ALARM",
  };

  const getStatus = (inc) => {
    if (inc.is_false_alarm) return "false-alarm";
    if (inc.suspicion_score >= 0.7) return "confirmed";
    // score >= 0.55 (above detection threshold) but < 0.7 = pending review
    if (inc.suspicion_score >= 0.55) return "pending";
    return "false-alarm"; // very low score, treat as cleared
  };

  const formatTime = (ts) => {
    if (!ts) return "—";
    // ts = "2026-06-25 13:05:22"
    return ts.split(" ")[1] || ts;
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <span className="panel-title-icon">◈</span>
          Forensic Audit Log
        </div>
        <span className="panel-badge live">● LIVE</span>
      </div>

      <div className="panel-body">
        {incidents.length === 0 ? (
          <div style={{
            padding: "40px",
            textAlign: "center",
            fontFamily: "var(--mono)",
            fontSize: "12px",
            color: "var(--text-muted)",
            letterSpacing: "1px",
          }}>
            NO INCIDENTS LOGGED — RUN BATCH DETECTION TO POPULATE
          </div>
        ) : (
          <table className="incident-table">
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Camera</th>
                <th>Zone</th>
                <th>Suspicion Score</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => {
                const status = getStatus(inc);
                return (
                  <tr
                    key={inc.id}
                    onClick={() => onSelect?.(inc)}
                    style={selectedId === inc.id ? {
                      background: "var(--cyan-dim)",
                      outline: "1px solid var(--cyan-border)",
                    } : {}}
                  >
                    <td className="id-cell">{inc.incident_label}</td>
                    <td className="camera-cell">{inc.camera_id}</td>
                    <td>{inc.zone || "General Area"}</td>
                    <td>
                      <div className="score-bar-wrap">
                        <div className="score-bar">
                          <div
                            className="score-bar-fill"
                            style={{ width: `${inc.suspicion_score * 100}%` }}
                          />
                        </div>
                        <span className="score-val">
                          {(inc.suspicion_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ fontFamily: "var(--mono)", fontSize: "12px" }}>
                      {formatTime(inc.timestamp)}
                    </td>
                    <td>
                      <span className={`status-pill ${status}`}>
                        {statusLabel[status]}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default IncidentTable;