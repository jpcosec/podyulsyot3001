import CytoscapeComponent from "react-cytoscapejs";

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

  const elementNodes = nodes.map((node, index) => ({
    data: {
      id: node.id,
      label: node.label,
      active: (props.activeNodeIds ?? []).includes(node.id) ? 1 : 0,
    },
    position: {
      x: 80 + (index % 5) * 140,
      y: 80 + Math.floor(index / 5) * 110,
    },
  }));
  const elementEdges = edges.map((edge) => ({
    data: { source: edge.source, target: edge.target, label: edge.label },
  }));

  return (
    <CytoscapeComponent
      key={`graph-${nodes.length}-${edges.length}`}
      elements={[...elementNodes, ...elementEdges]}
      style={{ width: "100%", height: "360px", borderRadius: "14px" }}
      stylesheet={[
        {
          selector: "node",
          style: {
            label: "data(label)",
            backgroundColor: "#123c69",
            color: "#f2efe7",
            textValign: "center",
            textHalign: "center",
            fontSize: 12,
            width: 60,
            height: 60,
          },
        },
        {
          selector: "node[active = 1]",
          style: {
            backgroundColor: "#b23a48",
          },
        },
        {
          selector: "edge",
          style: {
            label: "data(label)",
            width: 2,
            lineColor: "#7f8c8d",
            targetArrowColor: "#7f8c8d",
            targetArrowShape: "triangle",
            curveStyle: "bezier",
            fontSize: 10,
            color: "#2c3e50",
          },
        },
      ]}
      layout={{ name: "circle", fit: true, padding: 20 }}
    />
  );
}
