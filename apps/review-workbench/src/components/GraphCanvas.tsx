import { Component, type ErrorInfo, type ReactNode } from "react";

import { Graph } from "diagrammatic-ui";

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
    console.error("Diagrammatic-UI graph failed to render", error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

export function GraphCanvas(props: GraphCanvasProps): JSX.Element {
  const nodes =
    props.nodes ??
    [
      { id: "profile", label: "Profile" },
      { id: "job", label: "Job Posting" },
      { id: "match", label: "Match" },
    ];
  const edges =
    props.edges ??
    [
      { source: "profile", target: "match", label: "SATISFIED_BY" },
      { source: "job", target: "match", label: "HAS_REQUIREMENT" },
    ];

  const activeNodeSet = new Set(props.activeNodeIds ?? []);
  const graphData = {
    name: "review-graph",
    category: "pipeline",
    nodes: nodes.map((node) => ({
      id: node.id,
      name: node.label,
      type: activeNodeSet.has(node.id) ? "active" : "default",
      description: node.label,
    })),
    edges: edges.map((edge, index) => ({
      id: `${edge.source}->${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
    })),
  };

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
        <Graph
          data={graphData}
          theme="light"
          autoLayout="tree"
          width={920}
          height={360}
          interactionOptions={{
            selectionEnabled: true,
            multiSelectionEnabled: false,
            draggingEnabled: true,
            zoomEnabled: true,
            panningEnabled: true,
            fitViewOnInit: true,
          }}
          nodeStyleConfig={{
            type: "card",
            typeStyles: {
              default: { fill: "#123c69", stroke: "#123c69" },
              active: { fill: "#b23a48", stroke: "#b23a48" },
            },
          }}
        />
      </GraphErrorBoundary>
    </div>
  );
}
