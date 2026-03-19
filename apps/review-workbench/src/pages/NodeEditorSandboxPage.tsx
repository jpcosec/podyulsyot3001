import { memo, useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  addEdge,
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

type EditorState = "browse" | "focus" | "edit_node" | "edit_relation";

interface SimpleNodeData extends Record<string, unknown> {
  name: string;
  category: string;
  properties: Record<string, string>;
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
}

interface NodeDraft {
  id: string;
  name: string;
  category: string;
  properties: PropertyPair[];
}

interface EdgeDraft {
  id: string;
  relationType: string;
  properties: PropertyPair[];
}

const CATEGORY_COLORS: Record<string, string> = {
  person: "#e8d5b7",
  skill: "#d5e8b7",
  project: "#b7d5e8",
  publication: "#e8b7d5",
  concept: "#d9d6f8",
};

const CATEGORY_OPTIONS = ["person", "skill", "project", "publication", "concept"];

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
    return [{ key: "", value: "" }];
  }
  return entries.map(([key, value]) => ({ key, value }));
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

const SimpleNodeCard = memo(function SimpleNodeCard({ data }: NodeProps<SimpleNode>) {
  const nodeData = data as unknown as SimpleNodeData;
  const bg = CATEGORY_COLORS[nodeData.category] ?? "#e5e7eb";
  return (
    <div className="ne-node-simple" style={{ backgroundColor: bg }} title={tooltipFromProperties(nodeData.properties)}>
      <Handle type="target" position={Position.Left} />
      <span>{nodeData.name}</span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

const nodeTypes: NodeTypes = {
  simple: SimpleNodeCard,
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
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showLinkedEdges, setShowLinkedEdges] = useState(true);
  const [filterText, setFilterText] = useState("");

  const [savedSnapshot, setSavedSnapshot] = useState(() => serializeGraph(initial.nodes, initial.edges));

  const [nodeDraft, setNodeDraft] = useState<NodeDraft | null>(null);
  const [edgeDraft, setEdgeDraft] = useState<EdgeDraft | null>(null);

  const { fitView } = useReactFlow();

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

  const filteredNodeIds = useMemo(() => {
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

  const visibleEdges = useMemo(() => {
    return edges.filter((edge) => {
      const relationType = edge.data?.relationType ?? "linked";
      if (relationType === "linked" && !showLinkedEdges) {
        return false;
      }
      if (!filteredNodeIds.has(edge.source) || !filteredNodeIds.has(edge.target)) {
        return false;
      }
      return true;
    });
  }, [edges, showLinkedEdges, filteredNodeIds]);

  const displayNodes = useMemo(() => {
    return nodes
      .filter((node) => filteredNodeIds.has(node.id))
      .map((node) => {
        if (editorState === "focus" || editorState === "edit_node" || editorState === "edit_relation") {
          const active = node.id === focusedNodeId || neighborIds.has(node.id);
          return {
            ...node,
            className: active ? "ne-node-focused" : "ne-node-dimmed",
            draggable: active,
            selectable: active,
          };
        }
        return {
          ...node,
          className: "",
          draggable: true,
          selectable: true,
        };
      });
  }, [nodes, filteredNodeIds, editorState, focusedNodeId, neighborIds]);

  const displayEdges = useMemo(() => {
    return visibleEdges.map((edge) => {
      const inFocusModes =
        editorState === "focus" || editorState === "edit_node" || editorState === "edit_relation";
      if (!inFocusModes) {
        return edge;
      }
      const connected = edge.source === focusedNodeId || edge.target === focusedNodeId;
      return {
        ...edge,
        className: connected ? "" : "ne-edge-dimmed",
        animated: connected,
      };
    });
  }, [visibleEdges, editorState, focusedNodeId]);

  const openNodeEditor = useCallback(
    (nodeId: string) => {
      const node = nodes.find((item) => item.id === nodeId);
      if (!node) {
        return;
      }
      const nodeData = node.data as SimpleNodeData;
      setFocusedNodeId(node.id);
      setSelectedEdgeId(null);
      setNodeDraft({
        id: node.id,
        name: nodeData.name,
        category: nodeData.category,
        properties: pairsFromRecord(nodeData.properties),
      });
      setEditorState("edit_node");
    },
    [nodes],
  );

  const openEdgeEditor = useCallback(
    (edgeId: string) => {
      const edge = edges.find((item) => item.id === edgeId);
      if (!edge) {
        return;
      }
      setSelectedEdgeId(edge.id);
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
      setSelectedEdgeId(null);
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
    setFocusedNodeId(null);
    setSelectedEdgeId(null);
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
            data: { relationType: "linked", properties: {} },
          },
          prev,
        ) as SimpleEdge[],
      );
    },
    [setEdges],
  );

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

  const onSaveWorkspace = useCallback(() => {
    setSavedSnapshot(currentSnapshot);
  }, [currentSnapshot]);

  const onDiscardWorkspace = useCallback(() => {
    const parsed = JSON.parse(savedSnapshot) as { nodes: SimpleNode[]; edges: SimpleEdge[] };
    setNodes(parsed.nodes);
    setEdges(parsed.edges);
    setEditorState("browse");
    setFocusedNodeId(null);
    setSelectedEdgeId(null);
    setNodeDraft(null);
    setEdgeDraft(null);
  }, [savedSnapshot, setNodes, setEdges]);

  const onUnfocus = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    setEditorState("browse");
    setFocusedNodeId(null);
    setSelectedEdgeId(null);
    setTimeout(() => fitView({ duration: 320, padding: 0.1 }), 40);
  }, [editorState, fitView]);

  const onUpdateNodeDraftProperty = useCallback((index: number, field: "key" | "value", value: string) => {
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
      return { ...prev, properties: [...prev.properties, { key: "", value: "" }] };
    });
  }, []);

  const onRemoveNodeDraftProperty = useCallback((index: number) => {
    setNodeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const remaining = prev.properties.filter((_, i) => i !== index);
      return { ...prev, properties: remaining.length > 0 ? remaining : [{ key: "", value: "" }] };
    });
  }, []);

  const onSaveNodeDraft = useCallback(() => {
    if (!nodeDraft) {
      return;
    }
    const nextProperties = recordFromPairs(nodeDraft.properties);
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
    setNodeDraft(null);
    setEditorState("focus");
  }, [nodeDraft, setNodes]);

  const onDiscardNodeDraft = useCallback(() => {
    setNodeDraft(null);
    setEditorState("focus");
  }, []);

  const onUpdateEdgeDraftProperty = useCallback((index: number, field: "key" | "value", value: string) => {
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
      return { ...prev, properties: [...prev.properties, { key: "", value: "" }] };
    });
  }, []);

  const onRemoveEdgeDraftProperty = useCallback((index: number) => {
    setEdgeDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const remaining = prev.properties.filter((_, i) => i !== index);
      return { ...prev, properties: remaining.length > 0 ? remaining : [{ key: "", value: "" }] };
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
              <button type="button" className="ne-btn" disabled={!focusedNode || editorState === "edit_node"} onClick={() => focusedNode && openNodeEditor(focusedNode.id)}>
                Edit node
              </button>
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
              <label className="ne-checkbox-label">
                <input
                  type="checkbox"
                  checked={showLinkedEdges}
                  onChange={(event) => setShowLinkedEdges(event.target.checked)}
                />
                linked
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
            </div>
          </div>
        ) : null}
      </aside>

      <div className="ne-canvas-wrap">
        <ReactFlow<SimpleNode, SimpleEdge>
          nodes={displayNodes}
          edges={displayEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
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
                    <input
                      className="ne-input"
                      placeholder="value"
                      value={pair.value}
                      onChange={(event) => onUpdateNodeDraftProperty(index, "value", event.target.value)}
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
                    <input
                      className="ne-input"
                      placeholder="value"
                      value={pair.value}
                      onChange={(event) => onUpdateEdgeDraftProperty(index, "value", event.target.value)}
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
