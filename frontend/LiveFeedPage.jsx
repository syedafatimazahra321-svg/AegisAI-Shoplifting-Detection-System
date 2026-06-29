import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

const API = "http://localhost:8000";

function LiveFeedPage() {
  const [status, setStatus] = useState(null);
  const [info, setInfo]     = useState(null);
  const [limit, setLimit]   = useState(20);

  useEffect(() => {
    fetch(`${API}/api/videos/available`)
      .then((r) => r.json())
      .then(setInfo)
      .catch(() => {});
  }, []);

  useEffect(() => {
    const poll = () => {
      fetch(`${API}/api/batch-status`)
        .then((r) => r.json())
        .then(setStatus)
        .catch(() => {});
    };
    poll();
    const id = setInterval(poll, 1500);
    return () => clearInterval(id);
  }, []);

  const startBatch = () => {
    fetch(`${API}/api/batch-run?limit=${limit}`, { method: "POST" })
      .then((r) => r.json())
      .catch(() => {});
  };

  const progress = status?.total > 0
    ? Math.round((status.done / status.total) * 100)
    : 0;

  const isComplete = !status?.running && status?.done > 0;
  const hasErrors  = status?.errors?.length > 0;

  return (
    <div className="dashboard-layout">
      <Sidebar active="Live Feed" />
      <div className="dashboard-main">

        {/* Header */}
        <div className="header">
          <div className="header-left">
            <h1>LIVE FEED</h1>
            <div className="node-status">
              <div className="status-dot" style={{
                background: status?.running ? "var(--amber)" : "var(--green)",
                boxShadow: `0 0 8px ${status?.running ? "var(--amber)" : "var(--green)"}`,
              }} />
              {status?.running ? "BATCH PROCESSING IN PROGRESS" : "BATCH VIDEO PROCESSING"}
            </div>
          </div>
          {status?.running && (
            <div style={{
              fontFamily: "var(--mono)",
              fontSize: 16,
              color: "var(--amber)",
              fontWeight: "bold",
              letterSpacing: 1,
            }}>
              {status.done} / {status.total} PROCESSED
            </div>
          )}
        </div>

        {/* Two-column layout */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

          {/* Left — Dataset info + controls */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Dataset status */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">
                  <span className="panel-title-icon">📁</span>
                  Dataset Status
                </div>
              </div>
              <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 14 }}>
                {[
                  {
                    label: "Shoplifting_Class",
                    found: info?.folders?.shoplifting,
                    color: info?.folders?.shoplifting ? "var(--green)" : "var(--red)",
                  },
                  {
                    label: "Normal_Class",
                    found: info?.folders?.normal,
                    color: info?.folders?.normal ? "var(--green)" : "var(--red)",
                  },
                ].map(({ label, found, color }) => (
                  <div key={label} style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "12px 16px",
                    background: "var(--bg-panel)",
                    borderRadius: 6,
                    border: `1px solid ${color}33`,
                  }}>
                    <span style={{
                      fontFamily: "var(--mono)",
                      fontSize: 15,
                      color: "var(--text-secondary)",
                      fontWeight: "bold",
                    }}>
                      {label}
                    </span>
                    <span style={{
                      fontFamily: "var(--mono)",
                      fontSize: 14,
                      color,
                      fontWeight: "bold",
                    }}>
                      {found ? "✅ FOUND" : "❌ NOT FOUND"}
                    </span>
                  </div>
                ))}

                {/* Total videos big number */}
                <div style={{
                  padding: "16px",
                  background: "var(--bg-panel)",
                  borderRadius: 6,
                  border: "1px solid var(--cyan-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}>
                  <span style={{
                    fontFamily: "var(--mono)",
                    fontSize: 15,
                    color: "var(--text-muted)",
                    fontWeight: "bold",
                    letterSpacing: 1,
                  }}>
                    🎬 TOTAL VIDEOS AVAILABLE
                  </span>
                  <span style={{
                    fontFamily: "var(--mono)",
                    fontSize: 28,
                    color: "var(--cyan)",
                    fontWeight: "bold",
                  }}>
                    {info?.count ?? "—"}
                  </span>
                </div>
              </div>
            </div>

            {/* Batch controls */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">
                  <span className="panel-title-icon">▶</span>
                  Run Detection on Dataset
                </div>
              </div>
              <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>

                {/* Video count input */}
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <label style={{
                    fontFamily: "var(--mono)",
                    fontSize: 14,
                    color: "var(--text-muted)",
                    letterSpacing: 1,
                    fontWeight: "bold",
                    whiteSpace: "nowrap",
                  }}>
                    VIDEOS TO PROCESS
                  </label>
                  <input
                    type="number"
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    min={1}
                    max={info?.count || 100}
                    style={{
                      width: 90,
                      background: "var(--bg-panel)",
                      border: "1px solid var(--cyan-border)",
                      borderRadius: 4,
                      color: "var(--cyan)",
                      fontFamily: "var(--mono)",
                      fontSize: 18,
                      fontWeight: "bold",
                      padding: "8px 12px",
                      outline: "none",
                    }}
                  />
                </div>

                {/* Start button */}
                <button
                  onClick={startBatch}
                  disabled={status?.running}
                  style={{
                    padding: "16px 20px",
                    background: status?.running ? "transparent" : "var(--cyan-dim)",
                    border: `2px solid ${status?.running ? "var(--text-muted)" : "var(--cyan)"}`,
                    borderRadius: 6,
                    color: status?.running ? "var(--text-muted)" : "var(--cyan)",
                    fontFamily: "var(--mono)",
                    fontSize: 16,
                    fontWeight: "bold",
                    letterSpacing: 2,
                    cursor: status?.running ? "not-allowed" : "pointer",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => { if (!status?.running) e.currentTarget.style.background = "rgba(0,212,255,0.25)"; }}
                  onMouseLeave={(e) => { if (!status?.running) e.currentTarget.style.background = "var(--cyan-dim)"; }}
                >
                  {status?.running ? "⏳  PROCESSING..." : "▶  START BATCH DETECTION"}
                </button>

                {/* Note */}
                <div style={{
                  fontFamily: "var(--mono)",
                  fontSize: 13,
                  color: "var(--text-muted)",
                  letterSpacing: 0.5,
                  lineHeight: 1.7,
                }}>
                  ℹ Each video takes ~2–5 min on CPU.<br />
                  Dashboard auto-updates after batch completes.
                </div>
              </div>
            </div>
          </div>

          {/* Right — Progress + results */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Progress panel */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">
                  <span className="panel-title-icon">◈</span>
                  Batch Progress
                </div>
                {status?.running && (
                  <span style={{
                    fontFamily: "var(--mono)",
                    fontSize: 14,
                    color: "var(--amber)",
                    fontWeight: "bold",
                    animation: "blink 1.5s infinite",
                  }}>
                    ● RUNNING
                  </span>
                )}
              </div>
              <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>

                {/* Big progress number */}
                <div style={{ textAlign: "center" }}>
                  <div style={{
                    fontFamily: "var(--mono)",
                    fontSize: 72,
                    fontWeight: "bold",
                    color: isComplete ? "var(--green)" : status?.running ? "var(--amber)" : "var(--text-muted)",
                    lineHeight: 1,
                    transition: "color 0.3s",
                  }}>
                    {status?.total > 0 ? progress : 0}%
                  </div>
                  <div style={{
                    fontFamily: "var(--mono)",
                    fontSize: 14,
                    color: "var(--text-muted)",
                    marginTop: 8,
                    letterSpacing: 1,
                  }}>
                    {status?.done ?? 0} of {status?.total ?? 0} videos
                  </div>
                </div>

                {/* Progress bar */}
                <div style={{ height: 8, background: "var(--bg-hover)", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{
                    height: "100%",
                    width: `${status?.total > 0 ? progress : 0}%`,
                    background: isComplete
                      ? "var(--green)"
                      : "linear-gradient(90deg, var(--cyan), var(--red))",
                    borderRadius: 4,
                    transition: "width 0.5s",
                  }} />
                </div>

                {/* Currently processing */}
                {status?.running && status?.current && (
                  <div style={{
                    padding: "12px 16px",
                    background: "var(--bg-panel)",
                    borderRadius: 6,
                    border: "1px solid var(--amber-dim)",
                  }}>
                    <div style={{
                      fontFamily: "var(--mono)",
                      fontSize: 12,
                      color: "var(--text-muted)",
                      letterSpacing: 1,
                      marginBottom: 6,
                    }}>
                      CURRENTLY PROCESSING
                    </div>
                    <div style={{
                      fontFamily: "var(--mono)",
                      fontSize: 14,
                      color: "var(--amber)",
                      fontWeight: "bold",
                      wordBreak: "break-all",
                    }}>
                      {status.current}
                    </div>
                  </div>
                )}

                {/* Complete message */}
                {isComplete && !status?.running && (
                  <div style={{
                    padding: "14px 16px",
                    background: "var(--green-dim)",
                    border: "1px solid rgba(16,185,129,0.4)",
                    borderRadius: 6,
                    fontFamily: "var(--mono)",
                    fontSize: 15,
                    fontWeight: "bold",
                    color: "var(--green)",
                    textAlign: "center",
                    letterSpacing: 1,
                  }}>
                    ✅ BATCH COMPLETE — {status.done} videos processed
                    {hasErrors && (
                      <span style={{ color: "var(--amber)", display: "block", marginTop: 4, fontSize: 13 }}>
                        ⚠ {status.errors.length} errors (see below)
                      </span>
                    )}
                  </div>
                )}

                {/* Idle state */}
                {!status?.running && !isComplete && (
                  <div style={{
                    padding: "20px",
                    background: "var(--bg-panel)",
                    borderRadius: 6,
                    border: "1px solid var(--cyan-border)",
                    fontFamily: "var(--mono)",
                    fontSize: 14,
                    color: "var(--text-muted)",
                    textAlign: "center",
                    letterSpacing: 1,
                  }}>
                    AWAITING BATCH START
                  </div>
                )}
              </div>
            </div>

            {/* Errors panel — only shown when there are errors */}
            {hasErrors && (
              <div className="panel">
                <div className="panel-header">
                  <div className="panel-title" style={{ color: "var(--red)" }}>
                    <span className="panel-title-icon">⚠</span>
                    Errors ({status.errors.length})
                  </div>
                </div>
                <div style={{
                  padding: "16px",
                  maxHeight: 240,
                  overflowY: "auto",
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                }}>
                  {status.errors.map((e, i) => (
                    <div key={i} style={{
                      padding: "8px 12px",
                      background: "var(--red-dim)",
                      borderRadius: 4,
                      fontFamily: "var(--mono)",
                      fontSize: 13,
                      color: "var(--red)",
                      wordBreak: "break-all",
                    }}>
                      {e}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveFeedPage;