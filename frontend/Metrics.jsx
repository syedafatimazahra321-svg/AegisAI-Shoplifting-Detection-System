import { useEffect, useState } from "react";

const API = "http://localhost:8000";

function Metrics() {
  const [data, setData] = useState(null);

  const fetchMetrics = () => {
    fetch(`${API}/api/metrics`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {}); // silently fail, keep last state
  };

  useEffect(() => {
    fetchMetrics();
    const id = setInterval(fetchMetrics, 10000);
    return () => clearInterval(id);
  }, []);

  const metrics = [
    {
      label: "Total Detections",
      value: data?.total ?? "—",
      icon: "◉",
      variant: "cyan",
      delta: data ? `+${data.today_delta} today` : "loading...",
    },
    {
      label: "Pending Audit",
      value: data?.pending ?? "—",
      icon: "⏳",
      variant: "amber",
      delta: "needs review",
    },
    {
      label: "Verified Crimes",
      value: data?.verified ?? "—",
      icon: "⚠",
      variant: "red",
      delta: "confirmed",
    },
    {
      label: "False Alarms",
      value: data?.false_alarms ?? "—",
      icon: "✓",
      variant: "green",
      delta: "cleared",
    },
  ];

  return (
    <div className="metrics-grid">
      {metrics.map((m) => (
        <div className={`metric-card ${m.variant}`} key={m.label}>
          <div className="metric-icon">{m.icon}</div>
          <div className="metric-value">{m.value}</div>
          <div className="metric-label">{m.label}</div>
          <div className="metric-delta">{m.delta}</div>
        </div>
      ))}
    </div>
  );
}

export default Metrics;
