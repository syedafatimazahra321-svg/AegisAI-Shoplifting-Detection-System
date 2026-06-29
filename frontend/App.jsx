import { BrowserRouter, Routes, Route } from "react-router-dom";
import AuthPage       from "./pages/AuthPage";
import DashboardPage  from "./pages/DashboardPage";
import IncidentsPage  from "./pages/IncidentsPage";
import LiveFeedPage   from "./pages/LiveFeedPage";
import { ReportsPage } from "./pages/ReportsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<AuthPage />} />
        <Route path="/dashboard"  element={<DashboardPage />} />
        <Route path="/incidents"  element={<IncidentsPage />} />
        <Route path="/live-feed"  element={<LiveFeedPage />} />
        <Route path="/reports"    element={<ReportsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
