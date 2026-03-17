import { BrowserRouter, Route, Routes } from "react-router-dom";

import { JobStagePage } from "./pages/JobStagePage";
import { PortfolioPage } from "./pages/PortfolioPage";

export default function App(): JSX.Element {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="shell-bg">
        <main className="shell">
          <Routes>
            <Route path="/" element={<PortfolioPage />} />
            <Route path="/jobs/:source/:jobId" element={<JobStagePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
