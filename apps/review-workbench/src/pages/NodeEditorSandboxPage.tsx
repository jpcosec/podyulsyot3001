import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  addEdge,
  BaseEdge,
  Background,
  ConnectionMode,
  Controls,
  getBezierPath,
  Handle,
  type InternalNode,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useStore,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type EdgeProps,
  type Node,
  type NodeProps,
  type NodeTypes,
  type XYPosition,
} from "@xyflow/react";
import dagre from "dagre";
import "@xyflow/react/dist/style.css";

type EditorState = "browse" | "focus" | "edit_node" | "edit_relation";

interface SimpleNodeData extends Record<string, unknown> {
  name: string;
  category: string;
  properties: Record<string, string>;
  nodeId?: string;
  onEditNode?: (nodeId: string) => void;
}

interface SimpleEdgeData extends Record<string, unknown> {
  relationType: string;
  properties: Record<string, string>;
}

type SimpleNode = Node<SimpleNodeData>;
type SimpleEdge = Edge<SimpleEdgeData>;

interface PropertyPair {
  key: string;
  value: string;
  dataType: AttributeType;
}

type AttributeType =
  | "string"
  | "text_markdown"
  | "number"
  | "date"
  | "datetime"
  | "boolean"
  | "enum"
  | "enum_open";

interface NodeDraft {
  id: string;
  name: string;
  category: string;
  properties: PropertyPair[];
  removedRelationIds: string[];
}

interface EdgeDraft {
  id: string;
  relationType: string;
  properties: PropertyPair[];
}

interface ConnectMenuState {
  open: boolean;
  sourceNodeId: string;
  x: number;
  y: number;
}

interface NodeTemplate {
  name: string;
  category: string;
  defaults: Record<string, string>;
}

const CATEGORY_COLORS: Record<string, string> = {
  person: "#e8d5b7",
  skill: "#d5e8b7",
  project: "#b7d5e8",
  publication: "#e8b7d5",
  concept: "#d9d6f8",
};

const CATEGORY_OPTIONS = ["person", "skill", "project", "publication", "concept"];
const ATTRIBUTE_TYPES: AttributeType[] = [
  "string",
  "text_markdown",
  "number",
  "date",
  "datetime",
  "boolean",
  "enum",
  "enum_open",
];

const NODE_TEMPLATES: NodeTemplate[] = [
  { name: "Person", category: "person", defaults: { role: "new" } },
  { name: "Skill", category: "skill", defaults: { level: "basic" } },
  { name: "Project", category: "project", defaults: { stage: "draft" } },
  { name: "Publication", category: "publication", defaults: { year: "2026" } },
  { name: "Concept", category: "concept", defaults: { note: "new" } },
];

const DAGRE_NODE_WIDTH = 170;
const DAGRE_NODE_HEIGHT = 68;

function buildInitialGraph(): { nodes: SimpleNode[]; edges: SimpleEdge[] } {
  const nodes: SimpleNode[] = [
    {
      id: "n-alice",
      type: "simple",
      position: { x: 40, y: 60 },
      data: { name: "Alice", category: "person", properties: { role: "Engineer", location: "Berlin" } },
    },
    {
      id: "n-python",
      type: "simple",
      position: { x: 360, y: 40 },
      data: { name: "Python", category: "skill", properties: { level: "advanced" } },
    },
    {
      id: "n-react",
      type: "simple",
      position: { x: 360, y: 150 },
      data: { name: "React", category: "skill", properties: { level: "intermediate" } },
    },
    {
      id: "n-graph",
      type: "simple",
      position: { x: 680, y: 80 },
      data: { name: "Graph Editor", category: "project", properties: { stage: "prototype" } },
    },
    {
      id: "n-paper",
      type: "simple",
      position: { x: 680, y: 220 },
      data: { name: "Published Paper A", category: "publication", properties: { year: "2023" } },
    },
    {
      id: "n-ux",
      type: "simple",
      position: { x: 360, y: 280 },
      data: { name: "Node UX", category: "concept", properties: { status: "exploring" } },
    },
  ];

  const edges: SimpleEdge[] = [
    {
      id: "e-a-py",
      source: "n-alice",
      target: "n-python",
      data: { relationType: "linked", properties: { strength: "high" } },
    },
    {
      id: "e-a-react",
      source: "n-alice",
      target: "n-react",
      data: { relationType: "linked", properties: { strength: "medium" } },
    },
    {
      id: "e-react-graph",
      source: "n-react",
      target: "n-graph",
      data: { relationType: "linked", properties: { context: "frontend" } },
    },
  ];

  return { nodes, edges };
}

function pairsFromRecord(values: Record<string, string>): PropertyPair[] {
  const entries = Object.entries(values);
  if (entries.length === 0) {
    return [{ key: "", value: "", dataType: "string" }];
  }
  return entries.map(([key, value]) => ({ key, value, dataType: "string" }));
}

function recordFromPairs(values: PropertyPair[]): Record<string, string> {
  const result: Record<string, string> = {};
  for (const pair of values) {
    const key = pair.key.trim();
    if (!key) {
      continue;
    }
    result[key] = pair.value;
  }
  return result;
}

function tooltipFromProperties(values: Record<string, string>): string {
  return Object.entries(values)
    .map(([key, value]) => `${key}: ${value}`)
    .join("\n");
}

function PropertyValueInput({
  pair,
  onChange,
}: {
  pair: PropertyPair;
  onChange: (value: string) => void;
}): JSX.Element {
  if (pair.dataType === "text_markdown") {
    return (
      <textarea
        className="ne-input ne-input-textarea"
        placeholder="value"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "number") {
    return (
      <input
        className="ne-input"
        type="number"
        placeholder="value"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "date") {
    return (
      <input
        className="ne-input"
        type="date"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "datetime") {
    return (
      <input
        className="ne-input"
        type="datetime-local"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "boolean") {
    return (
      <label className="ne-checkbox-inline">
        <input
          type="checkbox"
          checked={pair.value === "true"}
          onChange={(event) => onChange(event.target.checked ? "true" : "false")}
        />
        {pair.value === "true" ? "true" : "false"}
      </label>
    );
  }

  if (pair.dataType === "enum") {
    return (
      <select className="ne-input" value={pair.value} onChange={(event) => onChange(event.target.value)}>
        <option value="">select...</option>
        <option value="low">low</option>
        <option value="medium">medium</option>
        <option value="high">high</option>
      </select>
    );
  }

  return (
    <input
      className="ne-input"
      placeholder={pair.dataType === "enum_open" ? "value (free enum)" : "value"}
      value={pair.value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

const SimpleNodeCard = memo(function SimpleNodeCard({ data, selected }: NodeProps<SimpleNode>) {
  const nodeData = data as unknown as SimpleNodeData;
  const bg = CATEGORY_COLORS[nodeData.category] ?? "#e5e7eb";
  const onEdit = () => {
    if (nodeData.onEditNode && nodeData.nodeId) {
      nodeData.onEditNode(nodeData.nodeId);
    }
  };
  return (
    <div
      className={`ne-node-simple ${selected ? "ne-node-simple-selected" : ""}`}
      style={{ backgroundColor: bg }}
      title={tooltipFromProperties(nodeData.properties)}
    >
      <Handle id="top" type="source" position={Position.Top} className="ne-node-handle" />
      <Handle id="right" type="source" position={Position.Right} className="ne-node-handle" />
      <Handle id="bottom" type="source" position={Position.Bottom} className="ne-node-handle" />
      <Handle id="left" type="source" position={Position.Left} className="ne-node-handle" />
      <span>{nodeData.name}</span>
      <button
        type="button"
        className={`ne-node-edit-chip ${selected ? "ne-node-edit-chip-visible" : ""}`}
        onMouseDown={(event) => event.stopPropagation()}
        onClick={(event) => {
          event.stopPropagation();
          onEdit();
        }}
      >
        Edit
      </button>
    </div>
  );
});

const nodeTypes: NodeTypes = {
  simple: SimpleNodeCard,
};

function getNodeIntersection(sourceNode: InternalNode, targetNode: InternalNode): XYPosition {
  const sourceWidth = sourceNode.measured.width ?? DAGRE_NODE_WIDTH;
  const sourceHeight = sourceNode.measured.height ?? DAGRE_NODE_HEIGHT;
  const targetWidth = targetNode.measured.width ?? DAGRE_NODE_WIDTH;
  const targetHeight = targetNode.measured.height ?? DAGRE_NODE_HEIGHT;
  const sourceCenterX = sourceNode.internals.positionAbsolute.x + sourceWidth / 2;
  const sourceCenterY = sourceNode.internals.positionAbsolute.y + sourceHeight / 2;
  const targetCenterX = targetNode.internals.positionAbsolute.x + targetWidth / 2;
  const targetCenterY = targetNode.internals.positionAbsolute.y + targetHeight / 2;

  const w = sourceWidth / 2;
  const h = sourceHeight / 2;
  const xx1 = (targetCenterX - sourceCenterX) / (2 * w) - (targetCenterY - sourceCenterY) / (2 * h);
  const yy1 = (targetCenterX - sourceCenterX) / (2 * w) + (targetCenterY - sourceCenterY) / (2 * h);
  const alpha = 1 / (Math.abs(xx1) + Math.abs(yy1));
  const xx3 = alpha * xx1;
  const yy3 = alpha * yy1;

  return {
    x: w * (xx3 + yy3) + sourceCenterX,
    y: h * (-xx3 + yy3) + sourceCenterY,
  };
}

function getEdgePosition(node: InternalNode, intersectionPoint: XYPosition): Position {
  const nX = Math.round(node.internals.positionAbsolute.x);
  const nY = Math.round(node.internals.positionAbsolute.y);
  const pX = Math.round(intersectionPoint.x);
  const pY = Math.round(intersectionPoint.y);

  if (pX <= nX + 1) return Position.Left;
  if (pX >= nX + (node.measured.width ?? 0) - 1) return Position.Right;
  if (pY <= nY + 1) return Position.Top;
  return Position.Bottom;
}

function getFloatingEdgeParams(source: InternalNode, target: InternalNode) {
  const sourceIntersection = getNodeIntersection(source, target);
  const targetIntersection = getNodeIntersection(target, source);

  return {
    sx: sourceIntersection.x,
    sy: sourceIntersection.y,
    tx: targetIntersection.x,
    ty: targetIntersection.y,
    sourcePosition: getEdgePosition(source, sourceIntersection),
    targetPosition: getEdgePosition(target, targetIntersection),
  };
}

const FloatingEdge = memo(function FloatingEdge({ id, source, target, style, markerEnd }: EdgeProps) {
  const sourceNode = useStore((store) => store.nodeLookup.get(source));
  const targetNode = useStore((store) => store.nodeLookup.get(target));

  if (!sourceNode || !targetNode) {
    return null;
  }

  const params = getFloatingEdgeParams(sourceNode, targetNode);
  const [path] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  return <BaseEdge id={id} path={path} style={style} markerEnd={markerEnd} />;
});

const edgeTypes = {
  floating: FloatingEdge,
};

function neighborsForNode(nodeId: string, edges: SimpleEdge[]): Set<string> {
  const related = new Set<string>();
  for (const edge of edges) {
    if (edge.source === nodeId) {
      related.add(edge.target);
    }
    if (edge.target === nodeId) {
      related.add(edge.source);
    }
  }
  return related;
}

function layoutAllDeterministic(nodes: SimpleNode[], edges: SimpleEdge[]): SimpleNode[] {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "LR", nodesep: 52, ranksep: 120, marginx: 24, marginy: 24 });

  [...nodes]
    .sort((a, b) => a.id.localeCompare(b.id))
    .forEach((node) => {
      graph.setNode(node.id, { width: DAGRE_NODE_WIDTH, height: DAGRE_NODE_HEIGHT });
    });

  [...edges]
    .sort((a, b) => a.id.localeCompare(b.id))
    .forEach((edge) => {
      graph.setEdge(edge.source, edge.target);
    });

  dagre.layout(graph);

  return nodes.map((node) => {
    const positioned = graph.node(node.id) as { x: number; y: number } | undefined;
    if (!positioned) {
      return node;
    }
    return {
      ...node,
      position: {
        x: positioned.x - DAGRE_NODE_WIDTH / 2,
        y: positioned.y - DAGRE_NODE_HEIGHT / 2,
      },
    };
  });
}

function layoutFocusNeighborhood(
  nodes: SimpleNode[],
  focusedNodeId: string,
  neighbors: Set<string>,
): SimpleNode[] {
  const center = { x: 420, y: 220 };
  const sortedNeighbors = [...neighbors].sort((a, b) => a.localeCompare(b));
  const baseRadius = 220;
  const radius = Math.max(baseRadius, sortedNeighbors.length * 36);

  const positions = new Map<string, { x: number; y: number }>();
  positions.set(focusedNodeId, center);

  sortedNeighbors.forEach((id, index) => {
    const angle = (index / Math.max(sortedNeighbors.length, 1)) * 2 * Math.PI - Math.PI / 2;
    positions.set(id, {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle),
    });
  });

  return nodes.map((node) => {
    const next = positions.get(node.id);
    if (!next) {
      return node;
    }
    return {
      ...node,
      position: next,
    };
  });
}

function serializeGraph(nodes: SimpleNode[], edges: SimpleEdge[]): string {
  return JSON.stringify({
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: node.data,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      data: edge.data,
    })),
  });
}

function NodeEditorInner(): JSX.Element {
  const initial = useMemo(() => buildInitialGraph(), []);
  const [nodes, setNodes, onNodesChange] = useNodesState<SimpleNode>(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<SimpleEdge>(initial.edges);

  const [editorState, setEditorState] = useState<EditorState>("browse");
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [hiddenRelationTypes, setHiddenRelationTypes] = useState<string[]>([]);
  const [filterText, setFilterText] = useState("");
  const [attributeFilterKey, setAttributeFilterKey] = useState("");
  const [attributeFilterValue, setAttributeFilterValue] = useState("");
  const [hideNonNeighbors, setHideNonNeighbors] = useState(false);

  const [savedSnapshot, setSavedSnapshot] = useState(() => serializeGraph(initial.nodes, initial.edges));

  const [nodeDraft, setNodeDraft] = useState<NodeDraft | null>(null);
  const [edgeDraft, setEdgeDraft] = useState<EdgeDraft | null>(null);
  const [connectMenu, setConnectMenu] = useState<ConnectMenuState | null>(null);
  const [pendingConnectSource, setPendingConnectSource] = useState<string | null>(null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const { fitView, screenToFlowPosition, getViewport, setViewport } = useReactFlow();

  const currentSnapshot = useMemo(() => serializeGraph(nodes, edges), [nodes, edges]);
  const dirty = currentSnapshot !== savedSnapshot;

  const focusedNode = useMemo(() => {
    if (!focusedNodeId) {
      return null;
    }
    return nodes.find((node) => node.id === focusedNodeId) ?? null;
  }, [focusedNodeId, nodes]);

  const neighborIds = useMemo(() => {
    if (!focusedNodeId) {
      return new Set<string>();
    }
    return neighborsForNode(focusedNodeId, edges);
  }, [focusedNodeId, edges]);

  const relationTypes = useMemo(() => {
    return [...new Set(edges.map((edge) => edge.data?.relationType ?? "linked"))];
  }, [edges]);

  const inFocusModes = editorState === "focus" || editorState === "edit_node" || editorState === "edit_relation";

  const filterablePropertyKeys = useMemo(() => {
    return [...new Set(nodes.flatMap((node) => Object.keys((node.data as SimpleNodeData).properties)))].sort((a, b) =>
      a.localeCompare(b),
    );
  }, [nodes]);

  const nodeNameById = useMemo(() => {
    return new Map<string, string>(
      nodes.map((node) => {
        const nodeData = node.data as SimpleNodeData;
        return [node.id, nodeData.name];
      }),
    );
  }, [nodes]);

  const nodeRelationPills = useMemo(() => {
    if (!nodeDraft) {
      return [] as Array<{ id: string; text: string }>;
    }
    return edges
      .filter((edge) => !nodeDraft.removedRelationIds.includes(edge.id))
      .filter((edge) => edge.source === nodeDraft.id || edge.target === nodeDraft.id)
      .map((edge) => {
        const relationType = edge.data?.relationType ?? "linked";
        const sourceName = nodeNameById.get(edge.source) ?? edge.source;
        const targetName = nodeNameById.get(edge.target) ?? edge.target;
        return {
          id: edge.id,
          text: `${relationType}: ${sourceName} -> ${targetName}`,
        };
      });
  }, [edges, nodeDraft, nodeNameById]);

  useEffect(() => {
    if (!isConnecting || !canvasRef.current) {
      return undefined;
    }

    let raf = 0;
    let pointer: { x: number; y: number } | null = null;

    const onMouseMove = (event: MouseEvent) => {
      pointer = { x: event.clientX, y: event.clientY };
    };

    const onTouchMove = (event: TouchEvent) => {
      const touch = event.touches[0];
      if (!touch) {
        return;
      }
      pointer = { x: touch.clientX, y: touch.clientY };
    };

    const tick = () => {
      if (!canvasRef.current || !pointer) {
        raf = window.requestAnimationFrame(tick);
        return;
      }

      const rect = canvasRef.current.getBoundingClientRect();
      const threshold = 44;
      const speed = 14;
      let deltaX = 0;
      let deltaY = 0;

      if (pointer.x < rect.left + threshold) {
        deltaX = speed;
      } else if (pointer.x > rect.right - threshold) {
        deltaX = -speed;
      }

      if (pointer.y < rect.top + threshold) {
        deltaY = speed;
      } else if (pointer.y > rect.bottom - threshold) {
        deltaY = -speed;
      }

      if (deltaX !== 0 || deltaY !== 0) {
        const viewport = getViewport();
        setViewport({ x: viewport.x + deltaX, y: viewport.y + deltaY, zoom: viewport.zoom }, { duration: 0 });
      }

      raf = window.requestAnimationFrame(tick);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("touchmove", onTouchMove);
    raf = window.requestAnimationFrame(tick);

    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("touchmove", onTouchMove);
    };
  }, [getViewport, isConnecting, setViewport]);

  const connectCandidates = useMemo(() => {
    if (!connectMenu) {
      return [] as SimpleNode[];
    }
    return nodes
      .filter((node) => node.id !== connectMenu.sourceNodeId)
      .sort((a, b) => a.id.localeCompare(b.id));
  }, [connectMenu, nodes]);

  const textFilteredNodeIds = useMemo(() => {
    const text = filterText.trim().toLowerCase();
    if (!text) {
      return new Set(nodes.map((node) => node.id));
    }
    return new Set(
      nodes
        .filter((node) => (node.data as SimpleNodeData).name.toLowerCase().includes(text))
        .map((node) => node.id),
    );
  }, [nodes, filterText]);

  const attributeFilteredNodeIds = useMemo(() => {
    const key = attributeFilterKey.trim();
    const value = attributeFilterValue.trim().toLowerCase();
    if (!key) {
      return new Set(nodes.map((node) => node.id));
    }
    return new Set(
      nodes
        .filter((node) => {
          const nodeData = node.data as SimpleNodeData;
          const propertyValue = nodeData.properties[key];
          if (propertyValue === undefined) {
            return false;
          }
          if (!value) {
            return true;
          }
          return propertyValue.toLowerCase().includes(value);
        })
        .map((node) => node.id),
    );
  }, [attributeFilterKey, attributeFilterValue, nodes]);

  const activeEditNodeIds = useMemo(() => {
    const active = new Set<string>();
    if (nodeDraft) {
      active.add(nodeDraft.id);
    }
    if (edgeDraft) {
      const edge = edges.find((item) => item.id === edgeDraft.id);
      if (edge) {
        active.add(edge.source);
        active.add(edge.target);
      }
    }
    return active;
  }, [edgeDraft, edges, nodeDraft]);

  const filteredNodeIds = useMemo(() => {
    if (inFocusModes) {
      return new Set(nodes.map((node) => node.id));
    }
    const next = new Set<string>();
    for (const node of nodes) {
      if (!textFilteredNodeIds.has(node.id)) {
        continue;
      }
      if (!attributeFilteredNodeIds.has(node.id)) {
        continue;
      }
      next.add(node.id);
    }
    activeEditNodeIds.forEach((id) => next.add(id));
    return next;
  }, [activeEditNodeIds, attributeFilteredNodeIds, inFocusModes, nodes, textFilteredNodeIds]);

  const relationTypeFilteredEdges = useMemo(() => {
    return edges.filter((edge) => {
      const relationType = edge.data?.relationType ?? "linked";
      if (hiddenRelationTypes.includes(relationType)) {
        return false;
      }
      return true;
    });
  }, [edges, hiddenRelationTypes]);

  const visibleEdges = useMemo(() => {
    return relationTypeFilteredEdges.filter((edge) => {
      if (!filteredNodeIds.has(edge.source) || !filteredNodeIds.has(edge.target)) {
        return false;
      }
      return true;
    });
  }, [filteredNodeIds, relationTypeFilteredEdges]);

  const openNodeEditor = useCallback(
    (nodeId: string) => {
      const node = nodes.find((item) => item.id === nodeId);
      if (!node) {
        return;
      }
      const nodeData = node.data as SimpleNodeData;
      setFocusedNodeId(node.id);
      setNodeDraft({
        id: node.id,
        name: nodeData.name,
        category: nodeData.category,
        properties: pairsFromRecord(nodeData.properties),
        removedRelationIds: [],
      });
      setEditorState("edit_node");
    },
    [nodes],
  );

  const displayNodes = useMemo(() => {
    return nodes
      .filter((node) => filteredNodeIds.has(node.id))
      .filter((node) => {
        if (!inFocusModes || !hideNonNeighbors) {
          return true;
        }
        return node.id === focusedNodeId || neighborIds.has(node.id);
      })
      .map((node) => {
        const nodeData = node.data as SimpleNodeData;
        if (inFocusModes) {
          const active = node.id === focusedNodeId || neighborIds.has(node.id);
          return {
            ...node,
            data: {
              ...nodeData,
              nodeId: node.id,
              onEditNode: openNodeEditor,
            },
            className: active ? "ne-node-focused" : "ne-node-dimmed",
            draggable: active,
            selectable: active,
          };
        }
        return {
          ...node,
          data: {
            ...nodeData,
            nodeId: node.id,
            onEditNode: openNodeEditor,
          },
          className: "",
          draggable: true,
          selectable: true,
        };
      });
  }, [nodes, filteredNodeIds, focusedNodeId, hideNonNeighbors, inFocusModes, neighborIds, openNodeEditor]);

  const displayEdges = useMemo(() => {
    return visibleEdges.map((edge) => {
      const baseEdge: SimpleEdge = {
        ...edge,
        type: "floating",
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "#334155",
        },
      };
      if (!inFocusModes) {
        return baseEdge;
      }
      const connected = edge.source === focusedNodeId || edge.target === focusedNodeId;
      if (hideNonNeighbors && !connected) {
        return { ...baseEdge, hidden: true };
      }
      return {
        ...baseEdge,
        className: connected ? "" : "ne-edge-dimmed",
        animated: connected,
      };
    });
  }, [visibleEdges, focusedNodeId, hideNonNeighbors, inFocusModes]);

  const openEdgeEditor = useCallback(
    (edgeId: string) => {
      const edge = edges.find((item) => item.id === edgeId);
      if (!edge) {
        return;
      }
      setFocusedNodeId(edge.source);
      setNodeDraft(null);
      setEdgeDraft({
        id: edge.id,
        relationType: edge.data?.relationType ?? "linked",
        properties: pairsFromRecord(edge.data?.properties ?? {}),
      });
      setEditorState("edit_relation");
      setTimeout(() => fitView({ nodes: [{ id: edge.source }], duration: 350, padding: 0.55 }), 50);
    },
    [edges, fitView],
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: SimpleNode) => {
      if (editorState === "edit_node" || editorState === "edit_relation") {
        return;
      }
      if (editorState === "focus") {
        const isActive = node.id === focusedNodeId || neighborIds.has(node.id);
        if (!isActive) {
          return;
        }
      }
      setFocusedNodeId(node.id);
      setEditorState("focus");
      setTimeout(() => fitView({ nodes: [{ id: node.id }], duration: 350, padding: 0.55 }), 50);
    },
    [editorState, focusedNodeId, neighborIds, fitView],
  );

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: SimpleNode) => {
      openNodeEditor(node.id);
    },
    [openNodeEditor],
  );

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: SimpleEdge) => {
      openEdgeEditor(edge.id);
    },
    [openEdgeEditor],
  );

  const onPaneClick = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    setConnectMenu(null);
    setFocusedNodeId(null);
    setEditorState("browse");
  }, [editorState]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) {
        return;
      }
      const newId = `e-${connection.source}-${connection.target}-${Date.now()}`;
      setEdges((prev) =>
        addEdge(
          {
            id: newId,
            ...connection,
            type: "floating",
            data: { relationType: "linked", properties: {} },
          },
          prev,
        ) as SimpleEdge[],
      );
      setConnectMenu(null);
      setPendingConnectSource(null);
    },
    [setEdges],
  );

  const onConnectStart = useCallback((_: unknown, params: { nodeId?: string | null }) => {
    setIsConnecting(true);
    setConnectMenu(null);
    setPendingConnectSource(params.nodeId ?? null);
  }, []);

  const onConnectEnd = useCallback(
    (event: MouseEvent | TouchEvent) => {
      const sourceNodeId = pendingConnectSource;
      setIsConnecting(false);
      setPendingConnectSource(null);
      if (!sourceNodeId) {
        return;
      }

      const target = event.target as HTMLElement | null;
      if (target?.closest(".react-flow__handle")) {
        return;
      }

      const point = "changedTouches" in event ? event.changedTouches[0] : event;
      setConnectMenu({
        open: true,
        sourceNodeId,
        x: point.clientX,
        y: point.clientY,
      });
    },
    [pendingConnectSource],
  );

  const onConnectToExistingNode = useCallback(
    (targetNodeId: string) => {
      if (!connectMenu) {
        return;
      }
      const edgeId = `e-${connectMenu.sourceNodeId}-${targetNodeId}-${Date.now()}`;
      setEdges((prev) =>
        addEdge(
          {
            id: edgeId,
            source: connectMenu.sourceNodeId,
            target: targetNodeId,
            type: "floating",
            data: { relationType: "linked", properties: {} },
          },
          prev,
        ) as SimpleEdge[],
      );
      setConnectMenu(null);
      setFocusedNodeId(targetNodeId);
      setEditorState("focus");
    },
    [connectMenu, setEdges],
  );

  const onCreateAndConnectNode = useCallback(() => {
    if (!connectMenu) {
      return;
    }
    const newNodeId = `n-new-${Date.now()}`;
    const flowPoint = screenToFlowPosition({ x: connectMenu.x, y: connectMenu.y });

    const newNodeData: SimpleNodeData = {
      name: `New Node ${nodes.length + 1}`,
      category: "concept",
      properties: { note: "edit me" },
    };

    setNodes((prev) => [
      ...prev,
      {
        id: newNodeId,
        type: "simple",
        position: flowPoint,
        data: newNodeData,
      },
    ]);

    const edgeId = `e-${connectMenu.sourceNodeId}-${newNodeId}-${Date.now()}`;
    setEdges((prev) =>
      addEdge(
        {
            id: edgeId,
            source: connectMenu.sourceNodeId,
            target: newNodeId,
            type: "floating",
            data: { relationType: "linked", properties: {} },
          },
          prev,
      ) as SimpleEdge[],
    );

    setConnectMenu(null);
    setFocusedNodeId(newNodeId);
    setNodeDraft({
      id: newNodeId,
      name: newNodeData.name,
      category: newNodeData.category,
      properties: pairsFromRecord(newNodeData.properties),
      removedRelationIds: [],
    });
    setEditorState("edit_node");
  }, [connectMenu, nodes.length, screenToFlowPosition, setEdges, setNodes]);

  const onAddNode = useCallback(() => {
    const id = `n-new-${Date.now()}`;
    setNodes((prev) => [
      ...prev,
      {
        id,
        type: "simple",
        position: { x: 140 + prev.length * 45, y: 120 + prev.length * 25 },
        data: {
          name: `New Node ${prev.length + 1}`,
          category: "concept",
          properties: { note: "edit me" },
        },
      },
    ]);
    setFocusedNodeId(id);
    setEditorState("focus");
  }, [setNodes]);

  const onTemplateDragStart = useCallback((event: React.DragEvent<HTMLButtonElement>, template: NodeTemplate) => {
    event.dataTransfer.setData("application/node-template", JSON.stringify(template));
    event.dataTransfer.effectAllowed = "copy";
  }, []);

  const onDragOverCanvas = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  }, []);

  const onDropOnCanvas = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const templateRaw = event.dataTransfer.getData("application/node-template");
      if (!templateRaw) {
        return;
      }
      let template: NodeTemplate;
      try {
        template = JSON.parse(templateRaw) as NodeTemplate;
      } catch (error) {
        console.error("Invalid node template payload", error);
        return;
      }
      const flowPoint = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const id = `n-new-${Date.now()}`;
      const nextName = `${template.name} ${nodes.length + 1}`;
      setNodes((prev) => [
        ...prev,
        {
          id,
          type: "simple",
          position: flowPoint,
          data: {
            name: nextName,
            category: template.category,
            properties: { ...template.defaults },
          },
        },
      ]);
      setFocusedNodeId(id);
      setEditorState("focus");
    },
    [nodes.length, screenToFlowPosition, setNodes],
  );

  const onLayoutAll = useCallback(() => {
    setNodes((prev) => layoutAllDeterministic(prev, edges));
    setTimeout(() => fitView({ duration: 380, padding: 0.14 }), 40);
  }, [edges, fitView, setNodes]);

  const onLayoutFocusNeighborhood = useCallback(() => {
    if (!focusedNodeId) {
      return;
    }
    setNodes((prev) => layoutFocusNeighborhood(prev, focusedNodeId, neighborsForNode(focusedNodeId, edges)));
    setTimeout(() => fitView({ nodes: [{ id: focusedNodeId }], duration: 420, padding: 0.55 }), 50);
  }, [edges, fitView, focusedNodeId, setNodes]);

  const onSaveWorkspace = useCallback(() => {
    setSavedSnapshot(currentSnapshot);
  }, [currentSnapshot]);

  const onDiscardWorkspace = useCallback(() => {
    const parsed = JSON.parse(savedSnapshot) as { nodes: SimpleNode[]; edges: SimpleEdge[] };
    setNodes(parsed.nodes);
    setEdges(parsed.edges);
    setEditorState("browse");
    setFocusedNodeId(null);
    setNodeDraft(null);
    setEdgeDraft(null);
  }, [savedSnapshot, setNodes, setEdges]);

  const onUnfocus = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    setEditorState("browse");
    setFocusedNodeId(null);
    setTimeout(() => fitView({ duration: 320, padding: 0.1 }), 40);
  }, [editorState, fitView]);

  const onUpdateNodeDraftProperty = useCallback((
    index: number,
    field: "key" | "value" | "dataType",
    value: string,
  ) => {
    setNodeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const next = [...prev.properties];
      next[index] = { ...next[index], [field]: value };
      return { ...prev, properties: next };
    });
  }, []);

  const onAddNodeDraftProperty = useCallback(() => {
    setNodeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      return { ...prev, properties: [...prev.properties, { key: "", value: "", dataType: "string" }] };
    });
  }, []);

  const onRemoveNodeDraftProperty = useCallback((index: number) => {
    setNodeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const remaining = prev.properties.filter((_, i) => i !== index);
      return {
        ...prev,
        properties: remaining.length > 0 ? remaining : [{ key: "", value: "", dataType: "string" }],
      };
    });
  }, []);

  const onSaveNodeDraft = useCallback(() => {
    if (!nodeDraft) {
      return;
    }
    const nextProperties = recordFromPairs(nodeDraft.properties);
    const removedRelationIds = new Set(nodeDraft.removedRelationIds);
    setNodes((prev) =>
      prev.map((node) => {
        if (node.id !== nodeDraft.id) {
          return node;
        }
        return {
          ...node,
          data: {
            ...(node.data as SimpleNodeData),
            name: nodeDraft.name || (node.data as SimpleNodeData).name,
            category: nodeDraft.category || (node.data as SimpleNodeData).category,
            properties: nextProperties,
          },
        };
      }),
    );
    if (removedRelationIds.size > 0) {
      setEdges((prev) => prev.filter((edge) => !removedRelationIds.has(edge.id)));
    }
    setNodeDraft(null);
    setEditorState("focus");
  }, [nodeDraft, setEdges, setNodes]);

  const onDiscardNodeDraft = useCallback(() => {
    setNodeDraft(null);
    setEditorState("focus");
  }, []);

  const onUpdateEdgeDraftProperty = useCallback((
    index: number,
    field: "key" | "value" | "dataType",
    value: string,
  ) => {
    setEdgeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const next = [...prev.properties];
      next[index] = { ...next[index], [field]: value };
      return { ...prev, properties: next };
    });
  }, []);

  const onAddEdgeDraftProperty = useCallback(() => {
    setEdgeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      return { ...prev, properties: [...prev.properties, { key: "", value: "", dataType: "string" }] };
    });
  }, []);

  const onRemoveEdgeDraftProperty = useCallback((index: number) => {
    setEdgeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const remaining = prev.properties.filter((_, i) => i !== index);
      return {
        ...prev,
        properties: remaining.length > 0 ? remaining : [{ key: "", value: "", dataType: "string" }],
      };
    });
  }, []);

  const onSaveEdgeDraft = useCallback(() => {
    if (!edgeDraft) {
      return;
    }
    const nextProperties = recordFromPairs(edgeDraft.properties);
    setEdges((prev) =>
      prev.map((edge) => {
        if (edge.id !== edgeDraft.id) {
          return edge;
        }
        return {
          ...edge,
          data: {
            relationType: edgeDraft.relationType || "linked",
            properties: nextProperties,
          },
        };
      }),
    );
    setEdgeDraft(null);
    setEditorState("focus");
  }, [edgeDraft, setEdges]);

  const onDiscardEdgeDraft = useCallback(() => {
    setEdgeDraft(null);
    setEditorState("focus");
  }, []);

  const onRemoveRelationFromNodeModal = useCallback(
    (edgeId: string) => {
      setNodeDraft((prev) => {
        if (!prev || prev.removedRelationIds.includes(edgeId)) {
          return prev;
        }
        return {
          ...prev,
          removedRelationIds: [...prev.removedRelationIds, edgeId],
        };
      });
    },
    [],
  );

  const stateLabel = useMemo(() => {
    if (editorState === "browse") {
      return "Browse";
    }
    if (editorState === "focus") {
      return focusedNode ? `Focus: ${(focusedNode.data as SimpleNodeData).name}` : "Focus";
    }
    if (editorState === "edit_node") {
      return "Edit Node";
    }
    return "Edit Relation";
  }, [editorState, focusedNode]);

  const onModeBadgeClick = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    onUnfocus();
  }, [editorState, onUnfocus]);

  return (
    <div className="ne-workspace">
      <aside className={`ne-sidebar ${sidebarOpen ? "" : "ne-sidebar-collapsed"}`}>
        <button type="button" className="ne-sidebar-toggle" onClick={() => setSidebarOpen((prev) => !prev)}>
          {sidebarOpen ? "\u25C0" : "\u25B6"}
        </button>
        {sidebarOpen ? (
          <div className="ne-sidebar-content">
            <div className="ne-state-section">
              <span className="ne-state-badge">{stateLabel}</span>
              <span className={`ne-dirty-dot ${dirty ? "ne-dirty-dot-on" : ""}`} title={dirty ? "Unsaved" : "Saved"} />
            </div>

            <div className="ne-control-row">
              <button type="button" className="ne-btn" disabled={editorState === "browse"} onClick={onUnfocus}>
                Unfocus
              </button>
              <span className="ne-inline-note">Edit is on-node</span>
            </div>

            <div className="ne-control-row">
              <button type="button" className="ne-btn ne-btn-primary" disabled={!dirty} onClick={onSaveWorkspace}>
                Save workspace
              </button>
              <button type="button" className="ne-btn" disabled={!dirty} onClick={onDiscardWorkspace}>
                Discard
              </button>
            </div>

            <div className="ne-control-row ne-control-row-single">
              <button type="button" className="ne-btn" onClick={onAddNode}>
                + Add node
              </button>
            </div>

            <div className="ne-filter-section">
              <h3>Drag palette</h3>
              <div className="ne-template-list">
                {NODE_TEMPLATES.map((template) => (
                  <button
                    key={template.name}
                    type="button"
                    draggable
                    className="ne-template-chip"
                    onDragStart={(event) => onTemplateDragStart(event, template)}
                  >
                    + {template.name}
                  </button>
                ))}
              </div>
              <p className="ne-template-hint">Drag a template into the canvas to create a node.</p>
            </div>

            <div className="ne-control-row">
              <button type="button" className="ne-btn" onClick={onLayoutAll}>
                Layout all
              </button>
              <button
                type="button"
                className="ne-btn"
                onClick={onLayoutFocusNeighborhood}
                disabled={!focusedNodeId}
              >
                Layout focus
              </button>
            </div>

            <div className="ne-stats">
              <p>
                Nodes: <strong>{nodes.length}</strong>
              </p>
              <p>
                Edges: <strong>{edges.length}</strong>
              </p>
              <p>
                Relation types: <strong>{relationTypes.join(", ") || "-"}</strong>
              </p>
            </div>

            <div className="ne-filter-section">
              <h3>Relations</h3>
              {relationTypes.length > 0 ? (
                relationTypes.map((relationType) => (
                  <label key={relationType} className="ne-checkbox-label">
                    <input
                      type="checkbox"
                      checked={!hiddenRelationTypes.includes(relationType)}
                      onChange={(event) => {
                        const isChecked = event.target.checked;
                        setHiddenRelationTypes((prev) => {
                          if (isChecked) {
                            return prev.filter((item) => item !== relationType);
                          }
                          if (prev.includes(relationType)) {
                            return prev;
                          }
                          return [...prev, relationType];
                        });
                      }}
                    />
                    {relationType}
                  </label>
                ))
              ) : (
                <p className="ne-empty-note">No relation types available.</p>
              )}
            </div>

            <div className="ne-filter-section">
              <h3>View options</h3>
              <label className="ne-checkbox-label">
                <input
                  type="checkbox"
                  checked={hideNonNeighbors}
                  onChange={(event) => setHideNonNeighbors(event.target.checked)}
                />
                Hide non-neighbors
              </label>
            </div>

            <div className="ne-filter-section">
              <h3>Filter nodes</h3>
              <input
                className="ne-input"
                placeholder="Filter by name"
                value={filterText}
                onChange={(event) => setFilterText(event.target.value)}
              />
              <select
                className="ne-input"
                value={attributeFilterKey}
                onChange={(event) => setAttributeFilterKey(event.target.value)}
              >
                <option value="">Any property key</option>
                {filterablePropertyKeys.map((key) => (
                  <option key={key} value={key}>
                    {key}
                  </option>
                ))}
              </select>
              <input
                className="ne-input"
                placeholder="Property value contains"
                value={attributeFilterValue}
                onChange={(event) => setAttributeFilterValue(event.target.value)}
                disabled={!attributeFilterKey}
              />
              <button
                type="button"
                className="ne-btn ne-btn-small"
                onClick={() => {
                  setFilterText("");
                  setAttributeFilterKey("");
                  setAttributeFilterValue("");
                }}
                disabled={!filterText && !attributeFilterKey && !attributeFilterValue}
              >
                Clear filters
              </button>
            </div>
          </div>
        ) : null}
      </aside>

      <div className="ne-canvas-wrap" ref={canvasRef}>
        <ReactFlow<SimpleNode, SimpleEdge>
          onDrop={onDropOnCanvas}
          onDragOver={onDragOverCanvas}
          nodes={displayNodes}
          edges={displayEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onConnectStart={onConnectStart}
          onConnectEnd={onConnectEnd}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          connectionMode={ConnectionMode.Loose}
          minZoom={0.1}
          fitView
          attributionPosition="bottom-left"
        >
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => CATEGORY_COLORS[(node.data as SimpleNodeData)?.category] ?? "#d1d5db"}
          />
          <Controls />
          <Background gap={20} size={1} />
        </ReactFlow>
        <button
          type="button"
          className="ne-mode-badge"
          onClick={onModeBadgeClick}
          title={
            editorState === "edit_node" || editorState === "edit_relation"
              ? "Finish edit to return to Browse"
              : "Return to Browse"
          }
          disabled={editorState === "edit_node" || editorState === "edit_relation"}
        >
          Mode: {stateLabel}
        </button>
        {connectMenu?.open ? (
          <div className="ne-connect-menu" style={{ left: connectMenu.x, top: connectMenu.y }}>
            <h4>Connect from {connectMenu.sourceNodeId}</h4>
            <button type="button" className="ne-btn ne-btn-small" onClick={onCreateAndConnectNode}>
              + Create new and connect
            </button>
            <div className="ne-connect-list">
              {connectCandidates.map((node) => (
                <button
                  key={node.id}
                  type="button"
                  className="ne-connect-item"
                  onClick={() => onConnectToExistingNode(node.id)}
                >
                  {(node.data as SimpleNodeData).name}
                </button>
              ))}
            </div>
            <button type="button" className="ne-btn" onClick={() => setConnectMenu(null)}>
              Cancel
            </button>
          </div>
        ) : null}
      </div>

      {editorState === "edit_node" && nodeDraft ? (
        <div className="ne-modal-backdrop">
          <div className="ne-modal-card">
            <h2>Edit node</h2>
            <label className="ne-field">
              <span>Name</span>
              <input
                className="ne-input"
                value={nodeDraft.name}
                onChange={(event) => setNodeDraft((prev) => (prev ? { ...prev, name: event.target.value } : prev))}
              />
            </label>
            <label className="ne-field">
              <span>Category</span>
              <select
                className="ne-input"
                value={nodeDraft.category}
                onChange={(event) => setNodeDraft((prev) => (prev ? { ...prev, category: event.target.value } : prev))}
              >
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <div className="ne-field">
              <span>Relations</span>
              <div className="ne-relation-pill-list">
                {nodeRelationPills.length > 0 ? (
                  nodeRelationPills.map((pill) => (
                    <div key={pill.id} className="ne-relation-pill-row">
                      <span className="ne-relation-pill-text">{pill.text}</span>
                      <button
                        type="button"
                        className="ne-remove-btn"
                        title="Remove relation"
                        onClick={() => onRemoveRelationFromNodeModal(pill.id)}
                      >
                        x
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="ne-empty-note">No relations for this node yet.</p>
                )}
              </div>
            </div>

            <div className="ne-field">
              <span>Properties</span>
              <div className="ne-property-list">
                {nodeDraft.properties.map((pair, index) => (
                  <div key={`${index}-${pair.key}`} className="ne-property-row">
                    <input
                      className="ne-input"
                      placeholder="key"
                      value={pair.key}
                      onChange={(event) => onUpdateNodeDraftProperty(index, "key", event.target.value)}
                    />
                    <select
                      className="ne-input"
                      value={pair.dataType}
                      onChange={(event) =>
                        onUpdateNodeDraftProperty(index, "dataType", event.target.value as AttributeType)
                      }
                    >
                      {ATTRIBUTE_TYPES.map((dataType) => (
                        <option key={dataType} value={dataType}>
                          {dataType}
                        </option>
                      ))}
                    </select>
                    <PropertyValueInput
                      pair={pair}
                      onChange={(value) => onUpdateNodeDraftProperty(index, "value", value)}
                    />
                    <button type="button" className="ne-remove-btn" onClick={() => onRemoveNodeDraftProperty(index)}>
                      x
                    </button>
                  </div>
                ))}
              </div>
              <button type="button" className="ne-btn ne-btn-small" onClick={onAddNodeDraftProperty}>
                + Add property
              </button>
            </div>

            <div className="ne-modal-actions">
              <button type="button" className="ne-btn ne-btn-primary" onClick={onSaveNodeDraft}>
                Save node
              </button>
              <button type="button" className="ne-btn" onClick={onDiscardNodeDraft}>
                Discard
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {editorState === "edit_relation" && edgeDraft ? (
        <div className="ne-modal-backdrop">
          <div className="ne-modal-card">
            <h2>Edit relation</h2>
            <label className="ne-field">
              <span>Type</span>
              <input
                className="ne-input"
                value={edgeDraft.relationType}
                onChange={(event) =>
                  setEdgeDraft((prev) => (prev ? { ...prev, relationType: event.target.value } : prev))
                }
              />
            </label>

            <div className="ne-field">
              <span>Relation properties</span>
              <div className="ne-property-list">
                {edgeDraft.properties.map((pair, index) => (
                  <div key={`${index}-${pair.key}`} className="ne-property-row">
                    <input
                      className="ne-input"
                      placeholder="key"
                      value={pair.key}
                      onChange={(event) => onUpdateEdgeDraftProperty(index, "key", event.target.value)}
                    />
                    <select
                      className="ne-input"
                      value={pair.dataType}
                      onChange={(event) =>
                        onUpdateEdgeDraftProperty(index, "dataType", event.target.value as AttributeType)
                      }
                    >
                      {ATTRIBUTE_TYPES.map((dataType) => (
                        <option key={dataType} value={dataType}>
                          {dataType}
                        </option>
                      ))}
                    </select>
                    <PropertyValueInput
                      pair={pair}
                      onChange={(value) => onUpdateEdgeDraftProperty(index, "value", value)}
                    />
                    <button type="button" className="ne-remove-btn" onClick={() => onRemoveEdgeDraftProperty(index)}>
                      x
                    </button>
                  </div>
                ))}
              </div>
              <button type="button" className="ne-btn ne-btn-small" onClick={onAddEdgeDraftProperty}>
                + Add property
              </button>
            </div>

            <div className="ne-modal-actions">
              <button type="button" className="ne-btn ne-btn-primary" onClick={onSaveEdgeDraft}>
                Save relation
              </button>
              <button type="button" className="ne-btn" onClick={onDiscardEdgeDraft}>
                Discard
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function NodeEditorSandboxPage(): JSX.Element {
  return (
    <section className="ne-page">
      <div className="breadcrumbs" style={{ padding: "0 24px" }}>
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to="/sandbox">Sandbox</Link>
        <span>/</span>
        <span>Node Editor</span>
      </div>
      <ReactFlowProvider>
        <NodeEditorInner />
      </ReactFlowProvider>
    </section>
  );
}
