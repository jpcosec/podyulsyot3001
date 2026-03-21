import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";

import { JobNodeEditorPage } from "./pages/JobNodeEditorPage";
import { JobStagePage } from "./pages/JobStagePage";
import { PortfolioPage } from "./pages/PortfolioPage";
import { CvGraphEditorPage } from "./sandbox/pages/CvGraphEditorPage";
import { NodeEditorPlanPage } from "./sandbox/pages/NodeEditorPlanPage";
import { NodeEditorSandboxPage } from "./sandbox/pages/NodeEditorSandboxPage";
import { SandboxPage } from "./sandbox/pages/SandboxPage";
import { TextTaggerPage } from "./sandbox/pages/TextTaggerPage";

function AppRoutes(): JSX.Element {
  const location = useLocation();
  const isFullscreenNodeEditor = location.pathname === "/sandbox/node_editor";

  const routes = (
    <Routes>
      <Route path="/" element={<PortfolioPage />} />
      <Route path="/jobs/:source/:jobId" element={<JobStagePage />} />
      <Route path="/jobs/:source/:jobId/node-editor" element={<JobNodeEditorPage />} />
      <Route path="/sandbox" element={<SandboxPage />} />
      <Route path="/sandbox/text_tagger" element={<TextTaggerPage />} />
      <Route path="/sandbox/cv_graph" element={<CvGraphEditorPage />} />
      <Route path="/sandbox/node_editor" element={<NodeEditorSandboxPage />} />
      <Route path="/sandbox/node_editor_plan" element={<NodeEditorPlanPage />} />
      <Route path="/text-tagger" element={<TextTaggerPage />} />
      <Route path="/cv-graph" element={<CvGraphEditorPage />} />
      <Route path="/cv-graph/entry/:entryId" element={<CvGraphEditorPage />} />
      <Route path="/cv-graph/skill/:skillId" element={<CvGraphEditorPage />} />
    </Routes>
  );

  if (isFullscreenNodeEditor) {
    return routes;
  }

  return (
    <div className="shell-bg">
      <main className="shell">{routes}</main>
    </div>
  );
}

export default function App(): JSX.Element {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppRoutes />
    </BrowserRouter>
  );
}
