import { Component, type ErrorInfo, type ReactNode } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface GraphNode {
  id: string;
  label: string;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

interface GraphCanvasProps {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  activeNodeIds?: string[];
}

interface GraphErrorBoundaryState {
  hasError: boolean;
}

class GraphErrorBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  GraphErrorBoundaryState
> {
  state: GraphErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): GraphErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown, errorInfo: ErrorInfo): void {
    console.error("GraphCanvas failed to render", error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

const DEFAULT_NODES: GraphNode[] = [
  { id: "profile", label: "Profile" },
  { id: "job", label: "Job Posting" },
  { id: "match", label: "Match" },
];

const DEFAULT_EDGES: GraphEdge[] = [
  { source: "profile", target: "match", label: "SATISFIED_BY" },
  { source: "job", target: "match", label: "HAS_REQUIREMENT" },
];

const DEFAULT_NODE_STYLE = {
  border: "1px solid #99f7ff",
  background: "#1a1c1e",
  color: "#eeeef0",
  borderRadius: 8,
  padding: "8px",
  width: 160,
  fontSize: 13,
  textAlign: "center" as const,
};

const ACTIVE_NODE_STYLE = {
  border: "1px solid #ffaa00",
  background: "#1d2022",
};

function toReactFlowNodes(graphNodes: GraphNode[], activeNodeIds: string[]): Node[] {
  const activeSet = new Set(activeNodeIds);
  return graphNodes.map((node, index) => ({
    id: node.id,
    position: {
      x: index === 0 ? 380 : 50 + index * 200,
      y: index === 0 ? 20 : 160,
    },
    data: { label: node.label },
    style: {
      ...DEFAULT_NODE_STYLE,
      ...(activeSet.has(node.id) ? ACTIVE_NODE_STYLE : {}),
    },
  }));
}

function toReactFlowEdges(graphEdges: GraphEdge[]): Edge[] {
  return graphEdges.map((edge, index) => ({
    id: `${edge.source}->${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    markerEnd: { type: MarkerType.ArrowClosed },
  }));
}

export function GraphCanvas(props: GraphCanvasProps): JSX.Element {
  const nodes = props.nodes ?? DEFAULT_NODES;
  const edges = props.edges ?? DEFAULT_EDGES;
  const activeNodeIds = props.activeNodeIds ?? [];

  const reactFlowNodes = toReactFlowNodes(nodes, activeNodeIds);
  const reactFlowEdges = toReactFlowEdges(edges);

  return (
    <div className="graph-shell">
      <GraphErrorBoundary
        fallback={
          <div className="graph-fallback" role="status" aria-live="polite">
            <p>
              Graph preview unavailable right now. Showing node/edge summary instead.
            </p>
            <div className="graph-fallback-grid">
              <div>
                <h4>Nodes</h4>
                <ul>
                  {nodes.map((node) => (
                    <li key={node.id}>{node.label}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4>Edges</h4>
                <ul>
                  {edges.map((edge, index) => (
                    <li key={`${edge.source}-${edge.target}-${index}`}>
                      {edge.source} -{edge.label}-&gt; {edge.target}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        }
      >
        <ReactFlowProvider>
          <ReactFlow
            nodes={reactFlowNodes}
            edges={reactFlowEdges}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            panOnDrag={false}
            zoomOnScroll={false}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            style={{ width: "100%", height: "100%" }}
          >
            <MiniMap pannable zoomable />
            <Controls />
            <Background gap={20} size={1} />
          </ReactFlow>
        </ReactFlowProvider>
      </GraphErrorBoundary>
    </div>
  );
}
