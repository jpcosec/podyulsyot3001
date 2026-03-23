import { useMemo, useCallback } from 'react';
import { useCvProfileGraph, useSaveCvGraph } from '../../features/base-cv/api/useCvProfileGraph';
import { cvProfileToGraph, graphToCvProfile } from '../../features/base-cv/lib/cvToGraph';
import { KnowledgeGraph } from './KnowledgeGraph';
import { Spinner } from '../../components/atoms/Spinner';
import type { SimpleNode, SimpleEdge } from './KnowledgeGraph';

export function BaseCvEditor() {
  const query = useCvProfileGraph();
  const saveMutation = useSaveCvGraph();

  const { nodes, edges } = useMemo(
    () => query.data ? cvProfileToGraph(query.data) : { nodes: [], edges: [] },
    [query.data],
  );

  const handleSave = useCallback((savedNodes: SimpleNode[], savedEdges: SimpleEdge[]) => {
    if (!query.data) return;
    saveMutation.mutate(graphToCvProfile(savedNodes, savedEdges, query.data));
  }, [query.data, saveMutation]);

  if (query.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (query.isError || !query.data) {
    return (
      <div className="p-6">
        <p className="font-mono text-error text-sm">CV_PROFILE_GRAPH_NOT_FOUND</p>
      </div>
    );
  }

  return (
    <KnowledgeGraph
      initialNodes={nodes}
      initialEdges={edges}
      onSave={handleSave}
    />
  );
}
