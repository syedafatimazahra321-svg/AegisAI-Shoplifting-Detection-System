const API = "http://localhost:8000";

function EvidencePanel({ incident }) {
  if (!incident) {
    return (
      <div className="panel evidence-panel">
        <div className="panel-header">
          <div className="panel-title">
            <span className="panel-title-icon">◉</span>
            Evidence Panel
          </div>
          <span className="panel-badge live">● REC</span>
        </div>
        <div className="panel-body">
          <div className="video-placeholder">
            <span className="video-icon">▶</span>
            <span>SELECT AN INCIDENT TO VIEW CLIP</span>
          </div>
          <div className="evidence-meta">
            <div className="meta-row">
              <span className="meta-label">Incident</span>
              <span className="meta-value" style={{ color: "var(--text-muted)" }}>—</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const videoUrl = `${API}/api/incidents/${incident.id}/video`;
  const score    = (incident.suspicion_score * 100).toFixed(0);
  const tags     = incident.behavior_tags || [];

  const zoneMultiplier =
    incident.zone === "Exit Zone"        ? "×2.0" :
    incident.zone === "High Value Shelf" ? "×1.5" : "×1.0";

  const isHighScore = incident.suspicion_score >= 0.7;

  return (
    <div className="panel evidence-panel">
      <div className="panel-header">
        <div className="panel-title">
          <span className="panel-title-icon">◉</span>
          Evidence Panel
        </div>
        <span className="panel-badge live">● REC</span>
      </div>

      <div className="panel-body">
        {incident.clip_path ? (
          <video
            key={incident.id}
            controls
            autoPlay
            loop
            muted
            style={{
              width: "100%",
              borderRadius: "6px",
              border: "1px solid var(--cyan-border)",
              background: "#000",
              maxHeight: "200px",
              objectFit: "cover",
            }}
          >
            <source src={videoUrl} type="video/mp4" />
            <source src={videoUrl} type="video/x-msvideo" />
            {/* Fallback: direct static path */}
            <source
              src={`${API}/clips/${incident.clip_path.split(/[\\/]/).pop()}`}
              type="video/mp4"
            />
            Your browser does not support this video format.
          </video>
        ) : (
          <div className="video-placeholder">
            <span className="video-icon">▶</span>
            <span>NO CLIP SAVED</span>
          </div>
        )}

        <div className="evidence-meta">
          <div className="meta-row">
            <span className="meta-label">Incident</span>
            <span className="meta-value">{incident.incident_label}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Camera</span>
            <span className="meta-value">{incident.camera_id}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Zone</span>
            <span className="meta-value">
              {incident.zone || "General Area"} {zoneMultiplier}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Score</span>
            <span
              className="meta-value"
              style={{ color: isHighScore ? "var(--red)" : "var(--amber)" }}
            >
              {score}%
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Time</span>
            <span className="meta-value" style={{ fontSize: "10px" }}>
              {incident.timestamp}
            </span>
          </div>
          {tags.length > 0 && (
            <div className="meta-row">
              <span className="meta-label">Behaviors</span>
              <div className="behavior-tags">
                {tags.map((t) => (
                  <span className="tag" key={t}>{t}</span>
                ))}
              </div>
            </div>
          )}
          {!incident.is_false_alarm && (
            <FalseAlarmButton incidentId={incident.id} />
          )}
        </div>
      </div>
    </div>
  );
}

function FalseAlarmButton({ incidentId }) {
  const [done, setDone] = useState(false);

  const mark = () => {
    fetch(`${API}/api/incidents/${incidentId}/false-alarm`, { method: "PATCH" })
      .then(() => setDone(true));
  };

  if (done) {
    return (
      <div style={{
        padding: "8px 10px",
        background: "var(--green-dim)",
        border: "1px solid rgba(16,185,129,0.3)",
        borderRadius: "4px",
        fontFamily: "var(--mono)",
        fontSize: "11px",
        color: "var(--green)",
        textAlign: "center",
        letterSpacing: "1px",
      }}>
        MARKED AS FALSE ALARM
      </div>
    );
  }

  return (
    <button
      onClick={mark}
      style={{
        width: "100%",
        padding: "8px",
        background: "transparent",
        border: "1px solid rgba(255,77,109,0.3)",
        borderRadius: "4px",
        color: "var(--red)",
        fontFamily: "var(--mono)",
        fontSize: "11px",
        letterSpacing: "1px",
        cursor: "pointer",
        transition: "background 0.2s",
      }}
      onMouseEnter={(e) => e.target.style.background = "var(--red-dim)"}
      onMouseLeave={(e) => e.target.style.background = "transparent"}
    >
      MARK AS FALSE ALARM
    </button>
  );
}

// need useState for FalseAlarmButton
import { useState } from "react";

export default EvidencePanel;
