import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppShell } from './components/layouts/AppShell';
import { JobWorkspaceShell } from './components/layouts/JobWorkspaceShell';
import { PortfolioDashboard } from './pages/global/PortfolioDashboard';
import { DataExplorer } from './pages/global/DataExplorer';
import { BaseCvEditor } from './pages/global/BaseCvEditor';
import { KnowledgeGraph } from './pages/global/KnowledgeGraph';
import { JobFlowInspector } from './pages/job/JobFlowInspector';
import { ScrapeDiagnostics } from './pages/job/ScrapeDiagnostics';
import { ExtractUnderstand } from './pages/job/ExtractUnderstand';
import { TranslateDiagnostics } from './pages/job/TranslateDiagnostics';
import { Match } from './pages/job/Match';
import { GenerateDocuments } from './pages/job/GenerateDocuments';
import { PackageDeployment } from './pages/job/PackageDeployment';
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true,      element: <PortfolioDashboard /> },
      { path: 'explorer', element: <DataExplorer /> },
      { path: 'cv',       element: <BaseCvEditor /> },
      { path: 'graph',    element: <KnowledgeGraph /> },
      {
        path: 'jobs/:source/:jobId',
        element: <JobWorkspaceShell />,
        children: [
          { index: true,          element: <JobFlowInspector /> },
          { path: 'scrape',       element: <ScrapeDiagnostics /> },
          { path: 'translate',    element: <TranslateDiagnostics /> },
          { path: 'extract',      element: <ExtractUnderstand /> },
          { path: 'match',        element: <Match /> },
          { path: 'sculpt',       element: <GenerateDocuments /> },
          { path: 'deployment',   element: <PackageDeployment /> },
        ],
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
