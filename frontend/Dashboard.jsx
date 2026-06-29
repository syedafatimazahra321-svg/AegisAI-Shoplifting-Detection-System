import { useState } from "react";
import Sidebar from "./Sidebar";
import Metrics from "./Metrics";
import IncidentTable from "./IncidentTable";
import EvidencePanel from "./EvidencePanel";

function Dashboard() {
  const [selectedIncident, setSelectedIncident] = useState(null);

  const now = new Date().toLocaleString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <div className="dashboard-main">
        <div className="header">
          <div className="header-left">
            <h1>AEGIS AI</h1>
            <div className="node-status">
              <div className="status-dot" />
              NODE ACTIVE — SURVEILLANCE RUNNING
            </div>
          </div>
          <div className="header-right">
            <span className="header-timestamp">{now}</span>
            <span className="header-badge">SYSTEM ONLINE</span>
          </div>
        </div>

        <Metrics />

        <div className="dashboard-grid">
          <IncidentTable
            onSelect={setSelectedIncident}
            selectedId={selectedIncident?.id}
          />
          <EvidencePanel incident={selectedIncident} />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
