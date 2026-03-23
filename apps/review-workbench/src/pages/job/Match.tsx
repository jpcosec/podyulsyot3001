import { useState, useMemo, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useViewMatch } from '../../features/job-pipeline/api/useViewMatch';
import { useGateDecide } from '../../features/job-pipeline/api/useGateDecide';
import { KnowledgeGraph } from '../global/KnowledgeGraph';
import { UnmappedSkillsPanel } from '../../features/job-pipeline/components/UnmappedSkillsPanel';
import { MatchDecisionModal } from '../../features/job-pipeline/components/MatchDecisionModal';
import { Spinner } from '../../components/atoms/Spinner';
import { matchPayloadToGraph } from '../../features/job-pipeline/lib/matchToGraph';
import type { GateDecisionPayload } from '../../types/api.types';
import type { SimpleNode, SimpleEdge } from '../global/KnowledgeGraph';

export function Match() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const matchQuery = useViewMatch(source!, jobId!);
  const gateDecide = useGateDecide(source!, jobId!, 'review_match');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentNodes, setCurrentNodes] = useState<SimpleNode[]>([]);
  const [currentEdges, setCurrentEdges] = useState<SimpleEdge[]>([]);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (matchQuery.data?.view === 'match') {
      return matchPayloadToGraph(matchQuery.data.data);
    }
    return { nodes: [], edges: [] };
  }, [matchQuery.data]);

  const unmappedNodes = useMemo(() => {
    const mappedTargets = new Set(currentEdges.map(e => e.target));
    return currentNodes.filter(
      n => n.data.properties['kind'] === 'profile' &&
           n.type === 'simple' &&
           !mappedTargets.has(n.id),
    );
  }, [currentNodes, currentEdges]);

  const handleGraphChange = useCallback((nodes: SimpleNode[], edges: SimpleEdge[]) => {
    setCurrentNodes(nodes);
    setCurrentEdges(edges);
  }, []);

  const handleDecide = (payload: GateDecisionPayload) => {
    gateDecide.mutate(payload, {
      onSuccess: () => setIsModalOpen(false),
    });
  };

  if (matchQuery.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (matchQuery.isError || !matchQuery.data || matchQuery.data.view !== 'match') {
    return <div className="p-6"><p className="font-mono text-error text-sm">MATCH_DATA_NOT_FOUND</p></div>;
  }

  return (
    <div className="relative flex h-full overflow-hidden">
      <div className="flex-1 min-w-0">
        <KnowledgeGraph
          initialNodes={initialNodes}
          initialEdges={initialEdges}
          onChange={handleGraphChange}
        />
      </div>

      <UnmappedSkillsPanel
        unmappedNodes={unmappedNodes}
        onSelectNode={() => {/* TODO: expose select API on KnowledgeGraph */}}
      />

      {/* DECIDE button — floats over the graph */}
      <button
        onClick={() => setIsModalOpen(true)}
        className="absolute bottom-6 left-6 z-50 font-mono text-[11px] tracking-widest border border-primary/60 text-primary bg-surface px-4 py-2 hover:bg-primary/10 transition-colors"
      >
        DECIDE
      </button>

      <MatchDecisionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDecide={handleDecide}
        isLoading={gateDecide.isPending}
      />
    </div>
  );
}
