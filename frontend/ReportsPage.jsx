import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

const API = "http://localhost:8000";

export function ReportsPage() {
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [success, setSuccess]   = useState(false);
  const [metrics, setMetrics]   = useState(null);

  // Pull live metrics to show a summary card
  useEffect(() => {
    fetch(`${API}/api/metrics`)
      .then((r) => r.json())
      .then(setMetrics)
      .catch(() => {});
  }, []);

  const downloadReport = () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    fetch(`${API}/api/report/generate`)
      .then((r) => {
        if (!r.ok) throw new Error("Generation failed — check backend terminal for details");
        return r.blob();
      })
      .then((blob) => {
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href     = url;
        a.download = `aegisai_report_${new Date().toISOString().slice(0,10)}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        setSuccess(true);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const today = new Date().toLocaleDateString("en-GB", {
    day: "2-digit", month: "long", year: "numeric",
  });

  const StatBox = ({ label, value, color }) => (
    <div style={{
      flex: 1,
      background: "var(--bg-panel)",
      border: `1px solid ${color}33`,
      borderRadius: 8,
      padding: "20px 16px",
      textAlign: "center",
    }}>
      <div style={{
        fontFamily: "var(--mono)",
        fontSize: 42,
        fontWeight: "bold",
        color,
        lineHeight: 1,
        marginBottom: 8,
      }}>
        {value ?? "—"}
      </div>
      <div style={{
        fontFamily: "var(--mono)",
        fontSize: 13,
        color: "var(--text-muted)",
        letterSpacing: 1,
        textTransform: "uppercase",
        fontWeight: "bold",
      }}>
        {label}
      </div>
    </div>
  );

  return (
    <div className="dashboard-layout">
      <Sidebar active="Reports" />
      <div className="dashboard-main">

        {/* Header */}
        <div className="header">
          <div className="header-left">
            <h1>REPORTS</h1>
            <div className="node-status">
              <div className="status-dot" />
              PDF GENERATION
            </div>
          </div>
          <div style={{
            fontFamily: "var(--mono)",
            fontSize: 16,
            color: "var(--text-muted)",
            letterSpacing: 1,
          }}>
            {today}
          </div>
        </div>

        {/* Live stats preview */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <span className="panel-title-icon">◉</span>
              Today's Summary
            </div>
            <span style={{
              fontFamily: "var(--mono)",
              fontSize: 13,
              color: "var(--green)",
              letterSpacing: 1,
            }}>
              ● LIVE DATA
            </span>
          </div>
          <div style={{ padding: "24px", display: "flex", gap: 16 }}>
            <StatBox label="Total Incidents"   value={metrics?.total}       color="var(--cyan)" />
            <StatBox label="Verified Crimes"   value={metrics?.verified}    color="var(--red)" />
            <StatBox label="Pending Review"    value={metrics?.pending}     color="var(--amber)" />
            <StatBox label="False Alarms"      value={metrics?.false_alarms} color="var(--green)" />
          </div>
        </div>

        {/* Report download */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <span className="panel-title-icon">◈</span>
              Daily Security Report
            </div>
          </div>
          <div style={{ padding: "28px 28px", display: "flex", gap: 32, alignItems: "flex-start" }}>

            {/* Left: description */}
            <div style={{ flex: 1 }}>
              <div style={{
                fontFamily: "var(--mono)",
                fontSize: 16,
                color: "var(--text-secondary)",
                lineHeight: 2,
                marginBottom: 24,
              }}>
                Generates a full PDF report containing:
              </div>
              {[
                "📋  Total incidents detected today",
                "✅  Verified crimes vs false alarm breakdown",
                "🕐  Busiest hour analysis",
                "🎥  Full incident log with scores & behaviors",
                "📊  Camera-wise incident distribution",
              ].map((item) => (
                <div key={item} style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "12px 16px",
                  marginBottom: 8,
                  background: "var(--bg-panel)",
                  borderRadius: 6,
                  border: "1px solid var(--cyan-border)",
                  fontFamily: "var(--mono)",
                  fontSize: 15,
                  color: "var(--text-secondary)",
                  letterSpacing: 0.5,
                }}>
                  {item}
                </div>
              ))}
            </div>

            {/* Right: download button + status */}
            <div style={{ width: 280, display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{
                padding: "20px",
                background: "var(--bg-panel)",
                border: "1px solid var(--cyan-border)",
                borderRadius: 8,
                textAlign: "center",
              }}>
                <div style={{
                  fontFamily: "var(--mono)",
                  fontSize: 13,
                  color: "var(--text-muted)",
                  letterSpacing: 1,
                  marginBottom: 6,
                }}>
                  REPORT DATE
                </div>
                <div style={{
                  fontFamily: "var(--mono)",
                  fontSize: 18,
                  color: "var(--cyan)",
                  fontWeight: "bold",
                }}>
                  {today}
                </div>
              </div>

              <button
                onClick={downloadReport}
                disabled={loading}
                style={{
                  padding: "16px 20px",
                  background: loading ? "transparent" : "var(--cyan-dim)",
                  border: `2px solid ${loading ? "var(--text-muted)" : "var(--cyan)"}`,
                  borderRadius: 6,
                  color: loading ? "var(--text-muted)" : "var(--cyan)",
                  fontFamily: "var(--mono)",
                  fontSize: 16,
                  fontWeight: "bold",
                  letterSpacing: 2,
                  cursor: loading ? "not-allowed" : "pointer",
                  transition: "all 0.2s",
                  width: "100%",
                }}
                onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = "rgba(0,212,255,0.25)"; }}
                onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = "var(--cyan-dim)"; }}
              >
                {loading ? "⏳  GENERATING..." : "⬇  DOWNLOAD PDF"}
              </button>

              {success && (
                <div style={{
                  padding: "14px 16px",
                  background: "var(--green-dim)",
                  border: "1px solid rgba(16,185,129,0.4)",
                  borderRadius: 6,
                  fontFamily: "var(--mono)",
                  fontSize: 14,
                  fontWeight: "bold",
                  color: "var(--green)",
                  textAlign: "center",
                  letterSpacing: 1,
                }}>
                  ✅ REPORT DOWNLOADED
                </div>
              )}

              {error && (
                <div style={{
                  padding: "14px 16px",
                  background: "var(--red-dim)",
                  border: "1px solid rgba(255,77,109,0.4)",
                  borderRadius: 6,
                  fontFamily: "var(--mono)",
                  fontSize: 13,
                  color: "var(--red)",
                  lineHeight: 1.6,
                }}>
                  ⚠ {error}
                </div>
              )}

              <div style={{
                padding: "14px 16px",
                background: "var(--bg-panel)",
                border: "1px solid var(--cyan-border)",
                borderRadius: 6,
                fontFamily: "var(--mono)",
                fontSize: 12,
                color: "var(--text-muted)",
                lineHeight: 1.8,
                letterSpacing: 0.5,
              }}>
                💡 Report saved to:<br />
                <span style={{ color: "var(--cyan)", fontSize: 11 }}>
                  incidents/daily_report.pdf
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

export default ReportsPage;