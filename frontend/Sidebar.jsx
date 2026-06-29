import { Link, useLocation } from "react-router-dom";

const navItems = [
  { icon: "⊞", label: "Dashboard", path: "/dashboard" },
  { icon: "⚠", label: "Incidents", path: "/incidents" },
  { icon: "◉", label: "Live Feed", path: "/live-feed" },
  { icon: "◈", label: "Reports",   path: "/reports" },
];

function Sidebar() {
  const location = useLocation();

  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-icon">🛡</span>
        <span className="brand-name">AegisAI</span>
      </div>

      <nav>
        <ul>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.label} className={isActive ? "active" : ""}>
                <Link
                  to={item.path}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    width: "100%",
                    textDecoration: "none",
                    color: "inherit",
                  }}
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="system-status">
          <div className="status-dot" />
          NODE ACTIVE
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
