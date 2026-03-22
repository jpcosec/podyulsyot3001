import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  type Node,
  type Edge,
  type Connection,
} from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import { RequirementNode } from './RequirementNode';
import { ProfileNode } from './ProfileNode';
import { EdgeScoreBadge } from './EdgeScoreBadge';
import type { GraphNode, GraphEdge } from '../../../types/api.types';

const NODE_WIDTH = 240;
const NODE_HEIGHT = 80;

const nodeTypes = {
  requirement: RequirementNode,
  profile: ProfileNode,
};

const edgeTypes = {
  scoreEdge: EdgeScoreBadge,
};

function layoutWithDagre(nodes: Node[], edges: Edge[]) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 120 });

  nodes.forEach(node => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  edges.forEach(edge => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  return nodes.map(node => {
    const pos = g.node(node.id);
    return { ...node, position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 } };
  });
}

interface Props {
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  onNodeClick: (node: GraphNode) => void;
  onEdgeClick: (edge: GraphEdge) => void;
  onAddEdge: (connection: { source: string; target: string }) => void;
}

export function MatchGraphCanvas({ graphNodes, graphEdges, onNodeClick, onEdgeClick, onAddEdge }: Props) {
  // Calculate max score per requirement for border color
  const reqScores = useMemo(() => {
    const scores: Record<string, number> = {};
    graphEdges.forEach(e => {
      const reqId = e.target;
      const s = e.score ?? 0;
      if (!scores[reqId] || s > scores[reqId]) scores[reqId] = s;
    });
    return scores;
  }, [graphEdges]);

  const initialNodes: Node[] = useMemo(() => graphNodes.map(n => ({
    id: n.id,
    type: n.kind === 'requirement' ? 'requirement' : 'profile',
    position: { x: 0, y: 0 },
    data: {
      label: n.label,
      score: n.kind === 'requirement' ? (reqScores[n.id] ?? 0) : undefined,
    },
  })), [graphNodes, reqScores]);

  const initialEdges: Edge[] = useMemo(() => graphEdges.map((e, i) => ({
    id: `edge-${i}`,
    source: e.source,
    target: e.target,
    type: 'scoreEdge',
    data: { score: e.score, reasoning: e.reasoning, edgeType: 'llm' as const },
  })), [graphEdges]);

  const laidOutNodes = useMemo(() => layoutWithDagre(initialNodes, initialEdges), [initialNodes, initialEdges]);

  const [nodes, , onNodesChange] = useNodesState(laidOutNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback((connection: Connection) => {
    setEdges(eds => addEdge({
      ...connection,
      type: 'scoreEdge',
      data: { score: null, edgeType: 'manual' as const },
    }, eds));
    if (connection.source && connection.target) {
      onAddEdge({ source: connection.source, target: connection.target });
    }
  }, [setEdges, onAddEdge]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onNodeClick={(_, node) => {
        const gn = graphNodes.find(n => n.id === node.id);
        if (gn) onNodeClick(gn);
      }}
      onEdgeClick={(_, edge) => {
        const ge = graphEdges.find((_, i) => `edge-${i}` === edge.id);
        if (ge) onEdgeClick(ge);
      }}
      fitView
      className="bg-surface node-connector"
    >
      <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="rgba(0,242,255,0.06)" />
      <Controls className="!bg-surface-container !border-outline/20 !shadow-none" />
    </ReactFlow>
  );
}
