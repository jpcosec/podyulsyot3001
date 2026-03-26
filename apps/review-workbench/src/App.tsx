import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layouts/AppShell';
import { KnowledgeGraph } from './pages/global/KnowledgeGraph';
import { useQuery } from '@tanstack/react-query';
import { graphDataProvider } from './features/graph-editor/lib/data-provider';
import './styles.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

function GraphPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['graph'],
    queryFn: () => graphDataProvider.getGraph(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-on-muted">Loading graph...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-error">Failed to load graph data</div>
      </div>
    );
  }

  return (
    <KnowledgeGraph 
      initialNodes={data.nodes as any} 
      initialEdges={data.edges as any} 
    />
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppShell>
        <GraphPage />
      </AppShell>
    </QueryClientProvider>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
