import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

const API = "http://localhost:8000";

function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [filter, setFilter]       = useState("all");

  const fetchIncidents = () => {
    fetch(`${API}/api/incidents?limit=200`)
      .then((r) => r.json())
      .then(setIncidents)
      .catch(() => {});
  };

  useEffect(() => {
    fetchIncidents();
    const id = setInterval(fetchIncidents, 10000);
    return () => clearInterval(id);
  }, []);

  const markFalseAlarm = (id) => {
    fetch(`${API}/api/incidents/${id}/false-alarm`, { method: "PATCH" })
      .then(() => fetchIncidents());
  };

  const getStatus = (inc) => {
    if (inc.is_false_alarm) return "false-alarm";
    if (inc.suspicion_score >= 0.7) return "confirmed";
    if (inc.suspicion_score >= 0.55) return "pending";
    return "false-alarm";
  };

  const filtered = incidents.filter((inc) => {
    if (filter === "all") return true;
    return getStatus(inc) === filter;
  });

  const statusLabel = {
    confirmed:     "CONFIRMED",
    pending:       "PENDING",
    "false-alarm": "FALSE ALARM",
  };

  const counts = {
    all:           incidents.length,
    confirmed:     incidents.filter((i) => getStatus(i) === "confirmed").length,
    pending:       incidents.filter((i) => getStatus(i) === "pending").length,
    "false-alarm": incidents.filter((i) => getStatus(i) === "false-alarm").length,
  };

  const FilterBtn = ({ value, label }) => (
    <button
      onClick={() => setFilter(value)}
      style={{
        padding: "8px 20px",
        background: filter === value ? "var(--cyan-dim)" : "transparent",
        border: `1px solid ${filter === value ? "var(--cyan)" : "var(--cyan-border)"}`,
        borderRadius: 4,
        color: filter === value ? "var(--cyan)" : "var(--text-muted)",
        fontFamily: "var(--mono)",
        fontSize: 14,           /* was 11 */
        fontWeight: filter === value ? "bold" : "normal",
        letterSpacing: 1,
        cursor: "pointer",
        transition: "all 0.2s",
      }}
    >
      {label}
      <span style={{
        marginLeft: 6,
        fontSize: 12,
        opacity: 0.7,
        color: filter === value ? "var(--cyan)" : "var(--text-muted)",
      }}>
        ({counts[value]})
      </span>
    </button>
  );

  return (
    <div className="dashboard-layout">
      <Sidebar active="Incidents" />
      <div className="dashboard-main">
        <div className="header">
          <div className="header-left">
            <h1>INCIDENTS</h1>
            <div className="node-status">
              <div className="status-dot" />
              {incidents.length} TOTAL LOGGED
            </div>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <FilterBtn value="all"         label="ALL" />
            <FilterBtn value="confirmed"   label="CONFIRMED" />
            <FilterBtn value="pending"     label="PENDING" />
            <FilterBtn value="false-alarm" label="FALSE ALARMS" />
          </div>
        </div>

        <div className="panel" style={{ flex: 1 }}>
          <div className="panel-header">
            <div className="panel-title">
              <span className="panel-title-icon">⚠</span>
              Incident Log
            </div>
            <span style={{
              fontFamily: "var(--mono)",
              fontSize: 15,               /* was 11 */
              color: "var(--text-muted)",
              fontWeight: "bold",
            }}>
              {filtered.length} results
            </span>
          </div>
          <div className="panel-body">
            {filtered.length === 0 ? (
              <div style={{
                padding: 60,
                textAlign: "center",
                fontFamily: "var(--mono)",
                fontSize: 16,
                color: "var(--text-muted)",
                letterSpacing: 2,
              }}>
                NO INCIDENTS FOUND
              </div>
            ) : (
              <table className="incident-table">
                <thead>
                  <tr>
                    <th>Incident ID</th>
                    <th>Timestamp</th>
                    <th>Camera</th>
                    <th>Zone</th>
                    <th>Score</th>
                    <th>Behaviors</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((inc) => {
                    const status = getStatus(inc);
                    return (
                      <tr key={inc.id}>
                        <td className="id-cell">{inc.incident_label}</td>

                        {/* Timestamp — was font-size 11, now 14 */}
                        <td style={{
                          fontFamily: "var(--mono)",
                          fontSize: 14,
                          color: "var(--text-secondary)",
                          whiteSpace: "nowrap",
                        }}>
                          {inc.timestamp}
                        </td>

                        <td className="camera-cell">{inc.camera_id}</td>
                        <td style={{ fontSize: 15 }}>{inc.zone || "General Area"}</td>

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

                        {/* Behaviors — was font-size 9, now 13 */}
                        <td>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                            {(inc.behavior_tags || []).map((t) => (
                              <span
                                key={t}
                                className="tag"
                                style={{ fontSize: 13 }}   /* was 9 */
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        </td>

                        <td>
                          <span className={`status-pill ${status}`}>
                            {statusLabel[status]}
                          </span>
                        </td>

                        {/* Action button — was font-size 9, now 13 */}
                        <td>
                          {!inc.is_false_alarm && (
                            <button
                              onClick={() => markFalseAlarm(inc.id)}
                              style={{
                                padding: "6px 12px",
                                background: "transparent",
                                border: "1px solid rgba(255,77,109,0.4)",
                                borderRadius: 4,
                                color: "var(--red)",
                                fontFamily: "var(--mono)",
                                fontSize: 13,             /* was 9 */
                                fontWeight: "bold",
                                letterSpacing: 1,
                                cursor: "pointer",
                                whiteSpace: "nowrap",
                                transition: "background 0.2s",
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.background = "var(--red-dim)"}
                              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                            >
                              FALSE ALARM
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default IncidentsPage;