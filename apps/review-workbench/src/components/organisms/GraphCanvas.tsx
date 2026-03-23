import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
  type ReactFlowInstance,
  type Connection,
} from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import { cn } from '../../utils/cn';

const NODE_WIDTH = 240;
const NODE_HEIGHT = 80;

export type GraphLayout = 'TB' | 'LR' | 'manual';

interface GraphNode {
  id: string;
  label: string;
  type?: string;
  data?: Record<string, unknown>;
  position?: { x: number; y: number };
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  score?: number;
  label?: string;
  data?: Record<string, unknown>;
}

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  nodeTypes?: NodeTypes;
  edgeTypes?: EdgeTypes;
  layout?: GraphLayout;
  direction?: 'TB' | 'LR';
  showControls?: boolean;
  showMiniMap?: boolean;
  className?: string;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  onConnect?: (connection: { source: string; target: string }) => void;
  onInit?: (instance: ReactFlowInstance) => void;
}

function layoutWithDagre(nodes: Node[], edges: Edge[], direction: 'TB' | 'LR'): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 40,
    ranksep: direction === 'TB' ? 100 : 120,
    edgesep: 20,
  });

  nodes.forEach(node => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  edges.forEach(edge => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  return nodes.map(node => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });
}

function toReactFlowNodes(graphNodes: GraphNode[], layout: GraphLayout, direction: 'TB' | 'LR'): Node[] {
  if (layout === 'manual') {
    return graphNodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position ?? { x: 0, y: 0 },
      data: { label: n.label, ...n.data },
    }));
  }

  const rfNodes: Node[] = graphNodes.map(n => ({
    id: n.id,
    type: n.type,
    position: { x: 0, y: 0 },
    data: { label: n.label, ...n.data },
  }));

  const rfEdges: Edge[] = []; // Empty for layout calculation

  return layoutWithDagre(rfNodes, rfEdges, direction);
}

function toReactFlowEdges(graphEdges: GraphEdge[]): Edge[] {
  return graphEdges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label ?? (e.score != null ? `${Math.round(e.score * 100)}%` : undefined),
    data: { score: e.score, ...e.data },
    type: e.score != null ? 'default' : 'smoothstep',
    animated: e.score != null && e.score > 0.7,
    style: e.score != null
      ? {
          stroke: e.score > 0.7 ? '#00f2ff' : e.score > 0.4 ? '#ffaa00' : '#ffb4ab',
          strokeWidth: 2,
        }
      : undefined,
  }));
}

export function GraphCanvas({
  nodes,
  edges,
  nodeTypes,
  edgeTypes,
  layout = 'LR',
  direction = 'LR',
  showControls = true,
  showMiniMap = false,
  className,
  onNodeClick,
  onEdgeClick,
  onConnect,
  onInit,
}: Props) {
  const rfNodes = useMemo(() => toReactFlowNodes(nodes, layout, direction), [nodes, layout, direction]);
  const rfEdges = useMemo(() => toReactFlowEdges(edges), [edges]);

  const [flowNodes, , onNodesChange] = useNodesState(rfNodes);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState(rfEdges);

  const handleConnect = onConnect
    ? (conn: Connection) => {
        if (conn.source && conn.target) {
          setFlowEdges(eds => addEdge(conn, eds));
          onConnect({ source: conn.source, target: conn.target });
        }
      }
    : undefined;

  const defaultNodeTypes: NodeTypes = {
    ...(nodeTypes ?? {}),
  };

  const defaultEdgeTypes: EdgeTypes = {
    ...(edgeTypes ?? {}),
  };

  return (
    <div className={cn('w-full h-full', className)}>
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={defaultNodeTypes}
        edgeTypes={defaultEdgeTypes}
        onNodeClick={(_, node) => onNodeClick?.(nodes.find(n => n.id === node.id)!)}
        onEdgeClick={(_, edge) => onEdgeClick?.(edges.find(e => e.id === edge.id)!)}
        onConnect={handleConnect}
        onInit={onInit}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
        }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="rgba(0, 242, 255, 0.08)"
        />
        {showControls && <Controls position="bottom-right" />}
        {showMiniMap && (
          <MiniMap
            nodeColor="rgba(0, 242, 255, 0.3)"
            maskColor="rgba(12, 14, 16, 0.8)"
            position="top-right"
          />
        )}
      </ReactFlow>
    </div>
  );
}
