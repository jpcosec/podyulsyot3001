import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useViewMatch } from '../../features/job-pipeline/api/useViewMatch';
import { useEvidenceBank } from '../../features/job-pipeline/api/useEvidenceBank';
import { useGateDecide } from '../../features/job-pipeline/api/useGateDecide';
import { useEditorState } from '../../features/job-pipeline/api/useEditorState';
import { MatchGraphCanvas } from '../../features/job-pipeline/components/MatchGraphCanvas';
import { EvidenceBankPanel } from '../../features/job-pipeline/components/EvidenceBankPanel';
import { MatchControlPanel } from '../../features/job-pipeline/components/MatchControlPanel';
import { MatchDecisionModal } from '../../features/job-pipeline/components/MatchDecisionModal';
import { Spinner } from '../../components/atoms/Spinner';
import type { GraphNode, GraphEdge, GateDecisionPayload } from '../../types/api.types';

export function Match() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const matchQuery = useViewMatch(source!, jobId!);
  const evidenceQuery = useEvidenceBank(source!, jobId!);
  const saveState = useEditorState(source!, jobId!, 'match');
  const gateDecide = useGateDecide(source!, jobId!, 'review_match');

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [manualEdges, setManualEdges] = useState<{ source: string; target: string }[]>([]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      saveState.mutate({ state: { manualEdges } });
    }
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      setIsModalOpen(true);
    }
  }, [saveState, manualEdges]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const handleDecide = (payload: GateDecisionPayload) => {
    gateDecide.mutate(payload, {
      onSuccess: () => setIsModalOpen(false),
    });
  };

  if (matchQuery.isLoading || evidenceQuery.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (matchQuery.isError || !matchQuery.data || matchQuery.data.view !== 'match') {
    return <div className="p-6"><p className="font-mono text-error text-sm">MATCH_DATA_NOT_FOUND</p></div>;
  }

  const { nodes: graphNodes, edges: graphEdges } = matchQuery.data.data;
  const evidenceItems = evidenceQuery.data?.items ?? [];

  return (
    <div className="flex h-full">
      <EvidenceBankPanel items={evidenceItems} />

      <div className="flex-1 min-w-0">
        <MatchGraphCanvas
          graphNodes={graphNodes}
          graphEdges={graphEdges}
          onNodeClick={node => { setSelectedNode(node); setSelectedEdge(null); }}
          onEdgeClick={edge => { setSelectedEdge(edge); setSelectedNode(null); }}
          onAddEdge={conn => setManualEdges(prev => [...prev, conn])}
        />
      </div>

      <MatchControlPanel
        selectedNode={selectedNode}
        selectedEdge={selectedEdge}
        onOpenDecisionModal={() => setIsModalOpen(true)}
        isSaving={saveState.isPending}
        onSave={() => saveState.mutate({ state: { manualEdges } })}
      />

      <MatchDecisionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDecide={handleDecide}
        isLoading={gateDecide.isPending}
      />
    </div>
  );
}
