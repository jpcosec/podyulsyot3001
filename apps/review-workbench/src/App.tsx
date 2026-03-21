import { BrowserRouter, Route, Routes } from "react-router-dom";

import { DataExplorerPage } from "./pages/DataExplorerPage";
import { DeploymentPage } from "./pages/DeploymentPage";
import { JobNodeEditorPage } from "./pages/JobNodeEditorPage";
import { JobStagePage } from "./pages/JobStagePage";
import { JobWorkspaceSidebar } from "./components/JobWorkspaceSidebar";
import { PortfolioPage } from "./pages/PortfolioPage";
import { CvGraphEditorPage } from "./sandbox/pages/CvGraphEditorPage";
import { NodeEditorPlanPage } from "./sandbox/pages/NodeEditorPlanPage";
import { NodeEditorSandboxPage } from "./sandbox/pages/NodeEditorSandboxPage";
import { SandboxPage } from "./sandbox/pages/SandboxPage";
import { TextTaggerPage } from "./sandbox/pages/TextTaggerPage";

function App(): JSX.Element {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<PortfolioPage />} />
        <Route path="/explorer" element={<DataExplorerPage />} />

        <Route path="/sandbox" element={<SandboxPage />} />
        <Route path="/sandbox/text_tagger" element={<TextTaggerPage />} />
        <Route path="/sandbox/cv_graph" element={<CvGraphEditorPage />} />
        <Route path="/sandbox/node_editor" element={<NodeEditorSandboxPage />} />
        <Route path="/sandbox/node_editor_plan" element={<NodeEditorPlanPage />} />

        <Route path="/text-tagger" element={<TextTaggerPage />} />
        <Route path="/cv-graph" element={<CvGraphEditorPage />} />
        <Route path="/cv-graph/entry/:entryId" element={<CvGraphEditorPage />} />
        <Route path="/cv-graph/skill/:skillId" element={<CvGraphEditorPage />} />

        <Route path="/jobs/:source/:jobId" element={<JobLayout><JobStagePage /></JobLayout>} />
        <Route path="/jobs/:source/:jobId/deployment" element={<JobLayout><DeploymentPage /></JobLayout>} />
        <Route path="/jobs/:source/:jobId/node-editor" element={<JobLayout><JobNodeEditorPage /></JobLayout>} />
      </Routes>
    </BrowserRouter>
  );
}

function JobLayout({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <div className="job-layout">
      <JobWorkspaceSidebar />
      <main className="job-layout-main">{children}</main>
    </div>
  );
}

export default App;
