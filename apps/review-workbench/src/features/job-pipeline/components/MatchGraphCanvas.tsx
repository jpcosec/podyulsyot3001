import { useMemo } from 'react';
import { GraphCanvas } from '../../../components/organisms/GraphCanvas';
import { RequirementNode } from './RequirementNode';
import { ProfileNode } from './ProfileNode';
import { EdgeScoreBadge } from './EdgeScoreBadge';
import type { GraphNode, GraphEdge } from '../../../types/api.types';

const MATCH_NODE_TYPES = { requirement: RequirementNode, profile: ProfileNode };
const MATCH_EDGE_TYPES = { scoreEdge: EdgeScoreBadge };

interface Props {
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  onNodeClick: (node: GraphNode) => void;
  onEdgeClick: (edge: GraphEdge) => void;
  onAddEdge: (connection: { source: string; target: string }) => void;
  searchQuery: string;
  focusedNodeId: string | null;
}

export function MatchGraphCanvas({
  graphNodes,
  graphEdges,
  onNodeClick,
  onEdgeClick,
  onAddEdge,
  searchQuery,
  focusedNodeId,
}: Props) {
  const reqScores = useMemo(() => {
    const scores: Record<string, number> = {};
    graphEdges.forEach(e => {
      const s = e.score ?? 0;
      if (!scores[e.target] || s > scores[e.target]!) scores[e.target] = s;
    });
    return scores;
  }, [graphEdges]);

  const nodes = useMemo(() => {
    const q = searchQuery.toLowerCase();
    return graphNodes.map(n => {
      const dimmed = q.length > 0 && !n.label.toLowerCase().includes(q);
      const highlighted = (q.length > 0 && n.label.toLowerCase().includes(q)) || focusedNodeId === n.id;
      return {
        id: n.id,
        label: n.label,
        type: n.kind === 'requirement' ? 'requirement' : 'profile',
        data: {
          score: n.kind === 'requirement' ? (reqScores[n.id] ?? 0) : undefined,
          dimmed,
          highlighted,
        },
      };
    });
  }, [graphNodes, reqScores, searchQuery, focusedNodeId]);

  const edges = useMemo(() => graphEdges.map((e, i) => ({
    id: `edge-${i}`,
    source: e.source,
    target: e.target,
    score: e.score ?? undefined,
    data: { score: e.score, reasoning: e.reasoning, edgeType: 'llm' as const },
  })), [graphEdges]);

  return (
    <GraphCanvas
      nodes={nodes}
      edges={edges}
      nodeTypes={MATCH_NODE_TYPES}
      edgeTypes={MATCH_EDGE_TYPES}
      layout="LR"
      direction="LR"
      showControls={true}
      onNodeClick={node => {
        const gn = graphNodes.find(n => n.id === node.id);
        if (gn) onNodeClick(gn);
      }}
      onEdgeClick={edge => {
        const ge = graphEdges.find((_, i) => `edge-${i}` === edge.id);
        if (ge) onEdgeClick(ge);
      }}
      onConnect={onAddEdge}
    />
  );
}
