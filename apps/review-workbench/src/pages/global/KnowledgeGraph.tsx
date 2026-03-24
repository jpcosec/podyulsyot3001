import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { cn } from "../../utils/cn";
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

type EditorState = "browse" | "focus" | "focus_relation" | "edit_node" | "edit_relation";

export interface SimpleNodeData extends Record<string, unknown> {
  name: string;
  category: string;
  properties: Record<string, string>;
  meta?: unknown;
  nodeId?: string;
  onEditNode?: (nodeId: string) => void;
}

export interface SimpleEdgeData extends Record<string, unknown> {
  relationType: string;
  properties: Record<string, string>;
}

export type SimpleNode = Node<SimpleNodeData>;
export type SimpleEdge = Edge<SimpleEdgeData>;

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

interface DeleteTarget {
  kind: "node" | "edge";
  title: string;
  description: string;
  nodes: SimpleNode[];
  edges: SimpleEdge[];
}

interface CopiedNodeState {
  node: SimpleNode;
  edges: SimpleEdge[];
}

interface HistoryActionBase {
  id: string;
  label: string;
}

type HistoryAction =
  | (HistoryActionBase & {
      kind: "create_elements";
      nodes: SimpleNode[];
      edges: SimpleEdge[];
    })
  | (HistoryActionBase & {
      kind: "delete_elements";
      nodes: SimpleNode[];
      edges: SimpleEdge[];
    })
  | (HistoryActionBase & {
      kind: "update_node";
      before: SimpleNode;
      after: SimpleNode;
    })
  | (HistoryActionBase & {
      kind: "update_edge";
      before: SimpleEdge;
      after: SimpleEdge;
    });

type SidebarSectionKey = "actions" | "filters" | "space" | "creation" | "vacant";

const CATEGORY_COLORS: Record<string, { border: string; bg: string }> = {
  // Base graph categories
  person:      { border: 'rgba(0,242,255,0.5)',   bg: 'rgba(0,242,255,0.07)' },
  skill:       { border: 'rgba(255,170,0,0.5)',   bg: 'rgba(255,170,0,0.07)' },
  project:     { border: 'rgba(0,242,255,0.25)',  bg: 'rgba(0,242,255,0.04)' },
  publication: { border: 'rgba(255,180,171,0.5)', bg: 'rgba(255,180,171,0.07)' },
  concept:     { border: 'rgba(116,117,120,0.5)', bg: 'rgba(116,117,120,0.07)' },
  document:    { border: 'rgba(0,242,255,0.6)',   bg: 'rgba(0,242,255,0.06)' },
  section:     { border: 'rgba(255,170,0,0.4)',   bg: 'rgba(255,170,0,0.05)' },
  entry:       { border: 'rgba(116,117,120,0.4)', bg: 'rgba(30,32,34,0.9)' },
  // Match view — requirement categories
  technical:      { border: 'rgba(0,242,255,0.6)',   bg: 'rgba(0,242,255,0.07)' },
  qualifications: { border: 'rgba(255,170,0,0.6)',   bg: 'rgba(255,170,0,0.07)' },
  soft_skills:    { border: 'rgba(100,220,130,0.6)', bg: 'rgba(100,220,130,0.07)' },
  communication:  { border: 'rgba(200,160,255,0.6)', bg: 'rgba(200,160,255,0.07)' },
  languages:      { border: 'rgba(255,200,80,0.6)',  bg: 'rgba(255,200,80,0.07)' },
  general:        { border: 'rgba(116,117,120,0.4)', bg: 'rgba(116,117,120,0.05)' },
  // Match view — profile categories
  education:      { border: 'rgba(255,170,0,0.7)',   bg: 'rgba(255,170,0,0.08)' },
  experience:     { border: 'rgba(0,242,255,0.7)',   bg: 'rgba(0,242,255,0.08)' },
  skills:         { border: 'rgba(100,220,130,0.7)', bg: 'rgba(100,220,130,0.08)' },
  publications:   { border: 'rgba(255,180,171,0.7)', bg: 'rgba(255,180,171,0.08)' },
  // Additional schema categories
  root:      { border: 'rgba(255,255,255,0.5)',  bg: 'rgba(255,255,255,0.04)' },
  abstract:  { border: 'rgba(116,117,120,0.4)',  bg: 'rgba(116,117,120,0.05)' },
  edge_node: { border: 'rgba(255,180,171,0.5)',  bg: 'rgba(255,180,171,0.07)' },
  value:     { border: 'rgba(116,117,120,0.3)',  bg: 'rgba(116,117,120,0.03)' },
};

const CATEGORY_OPTIONS = ["person", "skill", "project", "publication", "concept", "document", "section", "entry"];
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
  { name: "Document", category: "document", defaults: { title: "Untitled", type: "cv" } },
  { name: "Section", category: "section", defaults: { title: "New Section" } },
  { name: "Entry", category: "entry", defaults: { title: "", date: "" } },
];

function createEntityId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function upsertItemsById<T extends { id: string }>(existing: T[], items: T[]): T[] {
  const next = [...existing];
  const indexById = new Map(next.map((item, index) => [item.id, index]));
  for (const item of items) {
    const index = indexById.get(item.id);
    if (index === undefined) {
      next.push(item);
      indexById.set(item.id, next.length - 1);
      continue;
    }
    next[index] = item;
  }
  return next;
}

function removeItemsById<T extends { id: string }>(existing: T[], ids: string[]): T[] {
  const blocked = new Set(ids);
  return existing.filter((item) => !blocked.has(item.id));
}

function replaceItemById<T extends { id: string }>(existing: T[], item: T): T[] {
  return existing.map((current) => (current.id === item.id ? item : current));
}

function nextCopyName(baseName: string, existingNames: string[]): string {
  const usedNames = new Set(existingNames);
  const firstCandidate = `${baseName} (Copy)`;
  if (!usedNames.has(firstCandidate)) {
    return firstCandidate;
  }
  let index = 2;
  while (usedNames.has(`${baseName} (Copy ${index})`)) {
    index += 1;
  }
  return `${baseName} (Copy ${index})`;
}

function buildCopiedElements(copyState: CopiedNodeState, nodes: SimpleNode[]): { nodes: SimpleNode[]; edges: SimpleEdge[] } {
  const nodeData = copyState.node.data as SimpleNodeData;
  const existingNodeIds = new Set(nodes.map((node) => node.id));
  const newNodeId = createEntityId("n-copy");
  const nextName = nextCopyName(
    nodeData.name,
    nodes.map((node) => (node.data as SimpleNodeData).name),
  );
  const nextNode: SimpleNode = {
    ...copyState.node,
    id: newNodeId,
    position: {
      x: copyState.node.position.x + 48,
      y: copyState.node.position.y + 48,
    },
    selected: false,
    data: {
      ...nodeData,
      name: nextName,
    },
  };

  const nextEdges = copyState.edges
    .filter((edge) => {
      const siblingId = edge.source === copyState.node.id ? edge.target : edge.source;
      return siblingId === copyState.node.id || existingNodeIds.has(siblingId);
    })
    .map((edge) => ({
      ...edge,
      id: createEntityId("e-copy"),
      source: edge.source === copyState.node.id ? newNodeId : edge.source,
      target: edge.target === copyState.node.id ? newNodeId : edge.target,
      selected: false,
    }));

  return {
    nodes: [nextNode],
    edges: nextEdges,
  };
}

function SidebarSection({
  title,
  open,
  onToggle,
  children,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: JSX.Element | JSX.Element[] | null;
}): JSX.Element {
  return (
    <section className="border border-outline-variant rounded-xl overflow-hidden">
      <button type="button" className="flex items-center justify-between w-full px-3 py-2 font-mono text-[10px] text-on-muted hover:text-on-surface bg-transparent" onClick={onToggle}>
        <span>{title}</span>
        <span>{open ? "-" : "+"}</span>
      </button>
      {open ? <div className="px-3 pb-3 flex flex-col gap-2">{children}</div> : null}
    </section>
  );
}

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
        className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full min-h-[80px] resize-y"
        placeholder="value"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "number") {
    return (
      <input
        className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
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
        className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
        type="date"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "datetime") {
    return (
      <input
        className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
        type="datetime-local"
        value={pair.value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  if (pair.dataType === "boolean") {
    return (
      <label className="flex items-center gap-2 cursor-pointer text-[0.8rem]">
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
      <select className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full" value={pair.value} onChange={(event) => onChange(event.target.value)}>
        <option value="">select...</option>
        <option value="low">low</option>
        <option value="medium">medium</option>
        <option value="high">high</option>
      </select>
    );
  }

  return (
    <input
      className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
      placeholder={pair.dataType === "enum_open" ? "value (free enum)" : "value"}
      value={pair.value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

const SimpleNodeCard = memo(function SimpleNodeCard({ data, selected }: NodeProps<SimpleNode>) {
  const nodeData = data as unknown as SimpleNodeData;
  const color = CATEGORY_COLORS[nodeData.category] ?? { border: 'rgba(116,117,120,0.4)', bg: 'rgba(30,32,34,0.9)' };
  const onEdit = () => {
    if (nodeData.onEditNode && nodeData.nodeId) {
      nodeData.onEditNode(nodeData.nodeId);
    }
  };
  return (
    <div
      className={cn(
        "group border-2 border-outline-variant rounded-[10px] px-4 py-2.5 text-[0.83rem] font-medium text-center min-w-[110px] relative",
        selected && "ring-2 ring-primary/40",
      )}
      style={{ borderLeft: `4px solid ${color.border}`, background: color.bg, color: '#e2e2e5' }}
      title={tooltipFromProperties(nodeData.properties)}
    >
      <Handle id="top" type="source" position={Position.Top} className="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity" />
      <Handle id="right" type="source" position={Position.Right} className="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity" />
      <Handle id="bottom" type="source" position={Position.Bottom} className="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity" />
      <Handle id="left" type="source" position={Position.Left} className="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity" />
      <span>{nodeData.name}</span>
      <button
        type="button"
        className={cn(
          "absolute -top-2 -right-2 text-[0.65rem] bg-surface border border-outline-variant px-1 py-0.5 transition-opacity",
          selected ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto",
        )}
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

const GroupNode = memo(function GroupNode({ data, selected }: NodeProps<SimpleNode>) {
  const nodeData = data as unknown as SimpleNodeData;
  const color = CATEGORY_COLORS[nodeData.category] ?? { border: 'rgba(116,117,120,0.4)', bg: 'rgba(30,32,34,0.9)' };
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        border: `2px dashed ${color.border}`,
        background: color.bg,
        borderRadius: 8,
        position: 'relative',
        outline: selected ? `2px solid ${color.border}` : undefined,
      }}
    >
      <Handle id="top" type="source" position={Position.Top} className="opacity-0 hover:opacity-100 transition-opacity" />
      <Handle id="right" type="source" position={Position.Right} className="opacity-0 hover:opacity-100 transition-opacity" />
      <Handle id="bottom" type="source" position={Position.Bottom} className="opacity-0 hover:opacity-100 transition-opacity" />
      <Handle id="left" type="source" position={Position.Left} className="opacity-0 hover:opacity-100 transition-opacity" />
      <div
        style={{
          position: 'absolute',
          top: -20,
          left: 0,
          fontSize: '0.72rem',
          fontWeight: 600,
          color: color.border,
          fontFamily: 'JetBrains Mono, monospace',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
        }}
      >
        {nodeData.name}
      </div>
    </div>
  );
});

const nodeTypes: NodeTypes = {
  simple: SimpleNodeCard,
  group: GroupNode,
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

const SubFlowEdge = memo(function SubFlowEdge({ id, source, target, style, markerEnd }: EdgeProps) {
  const sourceNode = useStore((store) => store.nodeLookup.get(source));
  const targetNode = useStore((store) => store.nodeLookup.get(target));

  if (!sourceNode || !targetNode) return null;

  // ReactFlow stores positionAbsolute (canvas coords) for all nodes including children
  const params = getFloatingEdgeParams(sourceNode, targetNode);
  const [path] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={path}
      style={{ stroke: '#00f2ff', strokeWidth: 1.5, ...style }}
      markerEnd={markerEnd}
    />
  );
});

const edgeTypes = {
  floating: FloatingEdge,
  subflow: SubFlowEdge,
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

function snapshotNodePositions(nodes: SimpleNode[]): Record<string, XYPosition> {
  return Object.fromEntries(nodes.map((node) => [node.id, node.position]));
}

function applySavedNodePositions(nodes: SimpleNode[], savedPositions: Record<string, XYPosition>): SimpleNode[] {
  return nodes.map((node) => {
    const saved = savedPositions[node.id];
    if (!saved) {
      return node;
    }
    return {
      ...node,
      position: saved,
    };
  });
}

export interface KnowledgeGraphProps {
  initialNodes?: SimpleNode[];
  initialEdges?: SimpleEdge[];
  onSave?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void;
  onChange?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void;
  readOnly?: boolean;
}

function NodeEditorInner({ initialNodes, initialEdges, onSave, onChange, readOnly = false }: KnowledgeGraphProps): JSX.Element {
  const initial = useMemo(
    () => initialNodes ? { nodes: initialNodes, edges: initialEdges ?? [] } : buildInitialGraph(),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState<SimpleNode>(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<SimpleEdge>(initial.edges);

  const [editorState, setEditorState] = useState<EditorState>("browse");
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [focusedRelationId, setFocusedRelationId] = useState<string | null>(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [hiddenRelationTypes, setHiddenRelationTypes] = useState<string[]>([]);
  const [filterText, setFilterText] = useState("");
  const [attributeFilterKey, setAttributeFilterKey] = useState("");
  const [attributeFilterValue, setAttributeFilterValue] = useState("");
  const [hideNonNeighbors, setHideNonNeighbors] = useState(true);
  const [customLayoutPositions, setCustomLayoutPositions] = useState<Record<string, XYPosition> | null>(null);
  const [sectionOpen, setSectionOpen] = useState<Record<SidebarSectionKey, boolean>>({
    actions: true,
    filters: true,
    space: true,
    creation: true,
    vacant: true,
  });

  const [savedSnapshot, setSavedSnapshot] = useState(() => serializeGraph(initial.nodes, initial.edges));

  const [nodeDraft, setNodeDraft] = useState<NodeDraft | null>(null);
  const [edgeDraft, setEdgeDraft] = useState<EdgeDraft | null>(null);
  const [connectMenu, setConnectMenu] = useState<ConnectMenuState | null>(null);
  const [pendingConnectSource, setPendingConnectSource] = useState<string | null>(null);
  const [copiedNode, setCopiedNode] = useState<CopiedNodeState | null>(null);
  const [undoStack, setUndoStack] = useState<HistoryAction[]>([]);
  const [redoStack, setRedoStack] = useState<HistoryAction[]>([]);
  const [pendingDeleteTarget, setPendingDeleteTarget] = useState<DeleteTarget | null>(null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const { fitView, screenToFlowPosition, getViewport, setViewport } = useReactFlow();

  const currentSnapshot = useMemo(() => serializeGraph(nodes, edges), [nodes, edges]);
  const dirty = currentSnapshot !== savedSnapshot;

  // Auto-fit view on mount when readOnly (nodes have pre-computed positions)
  useEffect(() => {
    if (readOnly) {
      setTimeout(() => fitView({ duration: 350, padding: 0.12 }), 80);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Notify parent of any graph change (used by embedding pages like Match)
  useEffect(() => {
    onChange?.(nodes, edges);
  // Intentionally omit onChange from deps to avoid infinite loops — callers must memoize it
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  const focusedNode = useMemo(() => {
    if (!focusedNodeId) {
      return null;
    }
    return nodes.find((node) => node.id === focusedNodeId) ?? null;
  }, [focusedNodeId, nodes]);

  const focusedRelation = useMemo(() => {
    if (!focusedRelationId) {
      return null;
    }
    return edges.find((edge) => edge.id === focusedRelationId) ?? null;
  }, [edges, focusedRelationId]);

  const focusedRelationEndpointIds = useMemo(() => {
    if (!focusedRelation) {
      return new Set<string>();
    }
    return new Set([focusedRelation.source, focusedRelation.target]);
  }, [focusedRelation]);

  const neighborIds = useMemo(() => {
    if (!focusedNodeId) {
      return new Set<string>();
    }
    return neighborsForNode(focusedNodeId, edges);
  }, [focusedNodeId, edges]);

  const relationTypes = useMemo(() => {
    return [...new Set(edges.map((edge) => edge.data?.relationType ?? "linked"))];
  }, [edges]);

  const inFocusModes =
    editorState === "focus" ||
    editorState === "focus_relation" ||
    editorState === "edit_node" ||
    editorState === "edit_relation";

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

  const pushHistoryAction = useCallback((action: HistoryAction) => {
    setUndoStack((prev) => [action, ...prev]);
    setRedoStack([]);
  }, []);

  const applyUndoAction = useCallback((action: HistoryAction) => {
    if (action.kind === "create_elements") {
      setNodes((prev) => removeItemsById(prev, action.nodes.map((node) => node.id)));
      setEdges((prev) => removeItemsById(prev, action.edges.map((edge) => edge.id)));
      return;
    }
    if (action.kind === "delete_elements") {
      setNodes((prev) => upsertItemsById(prev, action.nodes));
      setEdges((prev) => upsertItemsById(prev, action.edges));
      return;
    }
    if (action.kind === "update_node") {
      setNodes((prev) => replaceItemById(prev, action.before));
      return;
    }
    setEdges((prev) => replaceItemById(prev, action.before));
  }, [setEdges, setNodes]);

  const applyRedoAction = useCallback((action: HistoryAction) => {
    if (action.kind === "create_elements") {
      setNodes((prev) => upsertItemsById(prev, action.nodes));
      setEdges((prev) => upsertItemsById(prev, action.edges));
      return;
    }
    if (action.kind === "delete_elements") {
      setNodes((prev) => removeItemsById(prev, action.nodes.map((node) => node.id)));
      setEdges((prev) => removeItemsById(prev, action.edges.map((edge) => edge.id)));
      return;
    }
    if (action.kind === "update_node") {
      setNodes((prev) => replaceItemById(prev, action.after));
      return;
    }
    setEdges((prev) => replaceItemById(prev, action.after));
  }, [setEdges, setNodes]);

  const onUndo = useCallback(() => {
    const nextAction = undoStack[0];
    if (!nextAction) {
      return;
    }
    applyUndoAction(nextAction);
    setUndoStack((prev) => prev.slice(1));
    setRedoStack((prev) => [nextAction, ...prev]);
    setConnectMenu(null);
    setPendingDeleteTarget(null);
    setFocusedNodeId(null);
    setFocusedRelationId(null);
    setNodeDraft(null);
    setEdgeDraft(null);
    setEditorState("browse");
  }, [applyUndoAction, undoStack]);

  const onRedo = useCallback(() => {
    const nextAction = redoStack[0];
    if (!nextAction) {
      return;
    }
    applyRedoAction(nextAction);
    setRedoStack((prev) => prev.slice(1));
    setUndoStack((prev) => [nextAction, ...prev]);
    setConnectMenu(null);
    setPendingDeleteTarget(null);
    setFocusedNodeId(null);
    setFocusedRelationId(null);
    setNodeDraft(null);
    setEdgeDraft(null);
    setEditorState("browse");
  }, [applyRedoAction, redoStack]);

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

  const constraintFilteredNodeIds = useMemo(() => {
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
    return next;
  }, [attributeFilteredNodeIds, nodes, textFilteredNodeIds]);

  const visibleEdges = useMemo(() => {
    return relationTypeFilteredEdges.filter((edge) => {
      if (!filteredNodeIds.has(edge.source) || !filteredNodeIds.has(edge.target)) {
        return false;
      }
      return true;
    });
  }, [filteredNodeIds, relationTypeFilteredEdges]);

  const vacantCandidateNodes = useMemo(() => {
    if (!focusedNodeId) {
      return [] as SimpleNode[];
    }
    if (hiddenRelationTypes.includes("linked")) {
      return [] as SimpleNode[];
    }

    const connectedNodeIds = new Set<string>();
    for (const edge of edges) {
      if (edge.source === focusedNodeId) {
        connectedNodeIds.add(edge.target);
      }
      if (edge.target === focusedNodeId) {
        connectedNodeIds.add(edge.source);
      }
    }

    return nodes
      .filter((node) => node.id !== focusedNodeId)
      .filter((node) => !connectedNodeIds.has(node.id))
      .filter((node) => constraintFilteredNodeIds.has(node.id))
      .sort((a, b) => {
        const aName = (a.data as SimpleNodeData).name;
        const bName = (b.data as SimpleNodeData).name;
        return aName.localeCompare(bName);
      });
  }, [constraintFilteredNodeIds, edges, focusedNodeId, hiddenRelationTypes, nodes]);

  const openNodeEditor = useCallback(
    (nodeId: string) => {
      const node = nodes.find((item) => item.id === nodeId);
      if (!node) {
        return;
      }
      const nodeData = node.data as SimpleNodeData;
      setFocusedNodeId(node.id);
      setFocusedRelationId(null);
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

  const openRelationFocus = useCallback(
    (edgeId: string) => {
      const edge = edges.find((item) => item.id === edgeId);
      if (!edge) {
        return;
      }
      setFocusedNodeId(null);
      setFocusedRelationId(edge.id);
      setNodeDraft(null);
      setEdgeDraft(null);
      setEditorState("focus_relation");
      setTimeout(() => fitView({ nodes: [{ id: edge.source }, { id: edge.target }], duration: 350, padding: 0.45 }), 50);
    },
    [edges, fitView],
  );

  const displayNodes = useMemo(() => {
    return nodes
      .filter((node) => filteredNodeIds.has(node.id))
      .filter((node) => {
        if (!inFocusModes || !hideNonNeighbors) {
          return true;
        }
        if (editorState === "focus_relation" || editorState === "edit_relation") {
          return focusedRelationEndpointIds.has(node.id);
        }
        return node.id === focusedNodeId || neighborIds.has(node.id);
      })
      .map((node) => {
        const nodeData = node.data as SimpleNodeData;
        if (inFocusModes) {
          const active =
            editorState === "focus_relation" || editorState === "edit_relation"
              ? focusedRelationEndpointIds.has(node.id)
              : node.id === focusedNodeId || neighborIds.has(node.id);
          return {
            ...node,
            data: {
              ...nodeData,
              nodeId: node.id,
              onEditNode: openNodeEditor,
            },
            className: active ? "opacity-100" : "opacity-30",
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
  }, [
    nodes,
    filteredNodeIds,
    focusedNodeId,
    focusedRelationEndpointIds,
    hideNonNeighbors,
    inFocusModes,
    neighborIds,
    openNodeEditor,
    editorState,
  ]);

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
      if (editorState === "focus_relation" || editorState === "edit_relation") {
        const active = edge.id === focusedRelationId;
        if (hideNonNeighbors && !active) {
          return { ...baseEdge, hidden: true };
        }
        return {
          ...baseEdge,
          className: active ? "opacity-100" : "opacity-30",
          animated: active,
          style: active ? { stroke: "#123c69", strokeWidth: 2.4 } : undefined,
        };
      }
      const connected = edge.source === focusedNodeId || edge.target === focusedNodeId;
      if (hideNonNeighbors && !connected) {
        return { ...baseEdge, hidden: true };
      }
      return {
        ...baseEdge,
        className: connected ? "" : "opacity-30",
        animated: connected,
      };
    });
  }, [visibleEdges, focusedNodeId, focusedRelationId, hideNonNeighbors, inFocusModes, editorState]);

  const openEdgeEditor = useCallback(
    (edgeId: string) => {
      const edge = edges.find((item) => item.id === edgeId);
      if (!edge) {
        return;
      }
      setFocusedNodeId(null);
      setFocusedRelationId(edge.id);
      setNodeDraft(null);
      setEdgeDraft({
        id: edge.id,
        relationType: edge.data?.relationType ?? "linked",
        properties: pairsFromRecord(edge.data?.properties ?? {}),
      });
      setEditorState("edit_relation");
      setTimeout(() => fitView({ nodes: [{ id: edge.source }, { id: edge.target }], duration: 350, padding: 0.45 }), 50);
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
      if (editorState === "focus_relation" && !focusedRelationEndpointIds.has(node.id)) {
        return;
      }
      setFocusedNodeId(node.id);
      setFocusedRelationId(null);
      setEditorState("focus");
      setTimeout(() => fitView({ nodes: [{ id: node.id }], duration: 350, padding: 0.55 }), 50);
    },
    [editorState, focusedNodeId, neighborIds, fitView, focusedRelationEndpointIds],
  );

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: SimpleNode) => {
      openNodeEditor(node.id);
    },
    [openNodeEditor],
  );

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: SimpleEdge) => {
      openRelationFocus(edge.id);
    },
    [openRelationFocus],
  );

  const onPaneClick = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    setConnectMenu(null);
    setFocusedNodeId(null);
    setFocusedRelationId(null);
    setEditorState("browse");
  }, [editorState]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) {
        return;
      }
      const newEdge: SimpleEdge = {
        id: createEntityId("e-link"),
        ...connection,
        type: "floating",
        data: { relationType: "linked", properties: {} },
      };
      setEdges((prev) =>
        addEdge(
          newEdge,
          prev,
        ) as SimpleEdge[],
      );
      pushHistoryAction({
        id: createEntityId("history"),
        kind: "create_elements",
        label: `Connected ${connection.source} -> ${connection.target}`,
        nodes: [],
        edges: [newEdge],
      });
      setConnectMenu(null);
      setPendingConnectSource(null);
      setFocusedRelationId(newEdge.id);
    },
    [pushHistoryAction, setEdges],
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
      const nextEdge: SimpleEdge = {
        id: createEntityId("e-link"),
        source: connectMenu.sourceNodeId,
        target: targetNodeId,
        type: "floating",
        data: { relationType: "linked", properties: {} },
      };
      setEdges((prev) =>
        addEdge(
          nextEdge,
          prev,
        ) as SimpleEdge[],
      );
      pushHistoryAction({
        id: createEntityId("history"),
        kind: "create_elements",
        label: `Connected ${connectMenu.sourceNodeId} -> ${targetNodeId}`,
        nodes: [],
        edges: [nextEdge],
      });
      setConnectMenu(null);
      setFocusedNodeId(targetNodeId);
      setFocusedRelationId(null);
      setEditorState("focus");
    },
    [connectMenu, pushHistoryAction, setEdges],
  );

  const onConnectFromVacantDrawer = useCallback(
    (targetNodeId: string) => {
      if (!focusedNodeId) {
        return;
      }
      const nextEdge: SimpleEdge = {
        id: createEntityId("e-link"),
        source: focusedNodeId,
        target: targetNodeId,
        type: "floating",
        data: { relationType: "linked", properties: {} },
      };
      setEdges((prev) =>
        addEdge(
          nextEdge,
          prev,
        ) as SimpleEdge[],
      );
      pushHistoryAction({
        id: createEntityId("history"),
        kind: "create_elements",
        label: `Connected ${focusedNodeId} -> ${targetNodeId}`,
        nodes: [],
        edges: [nextEdge],
      });
      setFocusedRelationId(null);
      setEditorState("focus");
    },
    [focusedNodeId, pushHistoryAction, setEdges],
  );

  const onCreateAndConnectNode = useCallback(() => {
    if (!connectMenu) {
      return;
    }
    const newNodeId = createEntityId("n-new");
    const flowPoint = screenToFlowPosition({ x: connectMenu.x, y: connectMenu.y });

    const newNodeData: SimpleNodeData = {
      name: `New Node ${nodes.length + 1}`,
      category: "concept",
      properties: { note: "edit me" },
    };

    const newNode: SimpleNode = {
      id: newNodeId,
      type: "simple",
      position: flowPoint,
      data: newNodeData,
    };

    const newEdge: SimpleEdge = {
      id: createEntityId("e-link"),
      source: connectMenu.sourceNodeId,
      target: newNodeId,
      type: "floating",
      data: { relationType: "linked", properties: {} },
    };

    setNodes((prev) => [...prev, newNode]);
    setEdges((prev) => addEdge(newEdge, prev) as SimpleEdge[]);
    pushHistoryAction({
      id: createEntityId("history"),
      kind: "create_elements",
      label: `Created ${newNodeData.name}`,
      nodes: [newNode],
      edges: [newEdge],
    });

    setConnectMenu(null);
    setFocusedNodeId(newNodeId);
    setFocusedRelationId(null);
    setNodeDraft({
      id: newNodeId,
      name: newNodeData.name,
      category: newNodeData.category,
      properties: pairsFromRecord(newNodeData.properties),
      removedRelationIds: [],
    });
    setEditorState("edit_node");
  }, [connectMenu, nodes.length, pushHistoryAction, screenToFlowPosition, setEdges, setNodes]);

  const onAddNode = useCallback(() => {
    const id = createEntityId("n-new");
    const nextNode: SimpleNode = {
      id,
      type: "simple",
      position: { x: 140 + nodes.length * 45, y: 120 + nodes.length * 25 },
      data: {
        name: `New Node ${nodes.length + 1}`,
        category: "concept",
        properties: { note: "edit me" },
      },
    };
    setNodes((prev) => [...prev, nextNode]);
    pushHistoryAction({
      id: createEntityId("history"),
      kind: "create_elements",
      label: `Created ${(nextNode.data as SimpleNodeData).name}`,
      nodes: [nextNode],
      edges: [],
    });
    setFocusedNodeId(id);
    setFocusedRelationId(null);
    setEditorState("focus");
  }, [nodes.length, pushHistoryAction, setNodes]);

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

      // Document template creates a 3-level nested structure
      if (template.category === "document") {
        const docId = createEntityId("doc");
        const sec1Id = createEntityId("sec");
        const sec2Id = createEntityId("sec");
        const ent1Id = createEntityId("entry");
        const ent2Id = createEntityId("entry");
        const newNodes: SimpleNode[] = [
          {
            id: docId,
            type: "group",
            position: flowPoint,
            style: { width: 600, height: 420 },
            data: { name: "Untitled CV", category: "document", properties: { type: "cv" } },
          },
          {
            id: sec1Id,
            type: "group",
            parentId: docId,
            extent: "parent",
            position: { x: 20, y: 60 },
            style: { width: 560, height: 160 },
            data: { name: "Introduction", category: "section", properties: {} },
          },
          {
            id: sec2Id,
            type: "group",
            parentId: docId,
            extent: "parent",
            position: { x: 20, y: 240 },
            style: { width: 560, height: 160 },
            data: { name: "Body", category: "section", properties: {} },
          },
          {
            id: ent1Id,
            type: "simple",
            parentId: sec1Id,
            extent: "parent",
            position: { x: 20, y: 50 },
            data: { name: "Entry 1", category: "entry", properties: { date: "" } },
          },
          {
            id: ent2Id,
            type: "simple",
            parentId: sec2Id,
            extent: "parent",
            position: { x: 20, y: 50 },
            data: { name: "Entry 2", category: "entry", properties: { date: "" } },
          },
        ];
        setNodes((prev) => [...prev, ...newNodes]);
        pushHistoryAction({
          id: createEntityId("history"),
          kind: "create_elements",
          label: "Created Document template",
          nodes: newNodes,
          edges: [],
        });
        setFocusedNodeId(docId);
        setFocusedRelationId(null);
        setEditorState("focus");
        return;
      }

      const id = createEntityId("n-new");
      const nextName = `${template.name} ${nodes.length + 1}`;
      const nextNode: SimpleNode = {
        id,
        type: "simple",
        position: flowPoint,
        data: {
          name: nextName,
          category: template.category,
          properties: { ...template.defaults },
        },
      };
      setNodes((prev) => [...prev, nextNode]);
      pushHistoryAction({
        id: createEntityId("history"),
        kind: "create_elements",
        label: `Created ${nextName}`,
        nodes: [nextNode],
        edges: [],
      });
      setFocusedNodeId(id);
      setFocusedRelationId(null);
      setEditorState("focus");
    },
    [nodes.length, pushHistoryAction, screenToFlowPosition, setNodes],
  );

  const onLayoutAll = useCallback(() => {
    setCustomLayoutPositions(snapshotNodePositions(nodes));
    setNodes((prev) => layoutAllDeterministic(prev, edges));
    setTimeout(() => fitView({ duration: 380, padding: 0.14 }), 40);
  }, [edges, fitView, nodes, setNodes]);

  const onLayoutFocusNeighborhood = useCallback(() => {
    if (!focusedNodeId) {
      return;
    }
    setCustomLayoutPositions(snapshotNodePositions(nodes));
    setNodes((prev) => layoutFocusNeighborhood(prev, focusedNodeId, neighborsForNode(focusedNodeId, edges)));
    setTimeout(() => fitView({ nodes: [{ id: focusedNodeId }], duration: 420, padding: 0.55 }), 50);
  }, [edges, fitView, focusedNodeId, nodes, setNodes]);

  const onLayoutCustom = useCallback(() => {
    if (!customLayoutPositions) {
      return;
    }
    setNodes((prev) => applySavedNodePositions(prev, customLayoutPositions));
    setTimeout(() => fitView({ duration: 380, padding: 0.14 }), 40);
  }, [customLayoutPositions, fitView, setNodes]);

  const onSaveWorkspace = useCallback(() => {
    setSavedSnapshot(currentSnapshot);
    onSave?.(nodes, edges);
  }, [currentSnapshot, onSave, nodes, edges]);

  const onDiscardWorkspace = useCallback(() => {
    const parsed = JSON.parse(savedSnapshot) as { nodes: SimpleNode[]; edges: SimpleEdge[] };
    setNodes(parsed.nodes);
    setEdges(parsed.edges);
    setEditorState("browse");
    setFocusedNodeId(null);
    setFocusedRelationId(null);
    setNodeDraft(null);
    setEdgeDraft(null);
    setUndoStack([]);
    setRedoStack([]);
    setPendingDeleteTarget(null);
  }, [savedSnapshot, setNodes, setEdges]);

  const onUnfocus = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    setEditorState("browse");
    setFocusedNodeId(null);
    setFocusedRelationId(null);
    setTimeout(() => fitView({ duration: 320, padding: 0.1 }), 40);
  }, [editorState, fitView]);

  const onCopyFocusedNode = useCallback(() => {
    if (editorState !== "focus" || !focusedNode) {
      return;
    }
    setCopiedNode({
      node: focusedNode,
      edges: edges.filter((edge) => edge.source === focusedNode.id || edge.target === focusedNode.id),
    });
  }, [editorState, edges, focusedNode]);

  const onPasteCopiedNode = useCallback(() => {
    if (editorState !== "focus" || !copiedNode) {
      return;
    }
    const created = buildCopiedElements(copiedNode, nodes);
    setNodes((prev) => upsertItemsById(prev, created.nodes));
    setEdges((prev) => upsertItemsById(prev, created.edges));
    pushHistoryAction({
      id: createEntityId("history"),
      kind: "create_elements",
      label: `Pasted ${created.nodes[0] ? ((created.nodes[0].data as SimpleNodeData).name ?? "node") : "node"}`,
      nodes: created.nodes,
      edges: created.edges,
    });
    setFocusedNodeId(created.nodes[0]?.id ?? null);
    setFocusedRelationId(null);
    setEditorState("focus");
  }, [copiedNode, editorState, nodes, pushHistoryAction, setEdges, setNodes]);

  const requestDeleteFocusedSelection = useCallback(() => {
    if (editorState === "focus" && focusedNode) {
      const incidentEdges = edges.filter((edge) => edge.source === focusedNode.id || edge.target === focusedNode.id);
      setPendingDeleteTarget({
        kind: "node",
        title: `Delete ${(focusedNode.data as SimpleNodeData).name}?`,
        description:
          incidentEdges.length > 0
            ? `This also removes ${incidentEdges.length} connected relation${incidentEdges.length === 1 ? "" : "s"}.`
            : "This removes the node from the workspace.",
        nodes: [focusedNode],
        edges: incidentEdges,
      });
      return;
    }
    if (editorState === "focus_relation" && focusedRelation) {
      setPendingDeleteTarget({
        kind: "edge",
        title: "Delete relation?",
        description: "This removes the selected relation from the workspace.",
        nodes: [],
        edges: [focusedRelation],
      });
    }
  }, [editorState, edges, focusedNode, focusedRelation]);

  const onConfirmDeleteSelection = useCallback(() => {
    if (!pendingDeleteTarget) {
      return;
    }
    const nodeIds = pendingDeleteTarget.nodes.map((node) => node.id);
    const edgeIds = pendingDeleteTarget.edges.map((edge) => edge.id);
    setNodes((prev) => removeItemsById(prev, nodeIds));
    setEdges((prev) => removeItemsById(prev, edgeIds));
    pushHistoryAction({
      id: createEntityId("history"),
      kind: "delete_elements",
      label: pendingDeleteTarget.kind === "node" ? `Deleted ${pendingDeleteTarget.nodes.length} node` : "Deleted relation",
      nodes: pendingDeleteTarget.nodes,
      edges: pendingDeleteTarget.edges,
    });
    setPendingDeleteTarget(null);
    setFocusedNodeId(null);
    setFocusedRelationId(null);
    setEditorState("browse");
  }, [pendingDeleteTarget, pushHistoryAction, setEdges, setNodes]);

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
    const previousNode = nodes.find((node) => node.id === nodeDraft.id);
    if (!previousNode) {
      return;
    }
    const nextProperties = recordFromPairs(nodeDraft.properties);
    const removedRelationIds = new Set(nodeDraft.removedRelationIds);
    const nextNode: SimpleNode = {
      ...previousNode,
      data: {
        ...(previousNode.data as SimpleNodeData),
        name: nodeDraft.name || (previousNode.data as SimpleNodeData).name,
        category: nodeDraft.category || (previousNode.data as SimpleNodeData).category,
        properties: nextProperties,
      },
    };
    setNodes((prev) =>
      prev.map((node) => {
        if (node.id !== nodeDraft.id) {
          return node;
        }
        return nextNode;
      }),
    );
    if (removedRelationIds.size > 0) {
      const removedEdges = edges.filter((edge) => removedRelationIds.has(edge.id));
      setEdges((prev) => prev.filter((edge) => !removedRelationIds.has(edge.id)));
      pushHistoryAction({
        id: createEntityId("history"),
        kind: "delete_elements",
        label: `Removed ${removedEdges.length} relation${removedEdges.length === 1 ? "" : "s"}`,
        nodes: [],
        edges: removedEdges,
      });
    }
    pushHistoryAction({
      id: createEntityId("history"),
      kind: "update_node",
      label: `Edited ${(nextNode.data as SimpleNodeData).name}`,
      before: previousNode,
      after: nextNode,
    });
    setNodeDraft(null);
    setEditorState("focus");
    setFocusedNodeId(nextNode.id);
    setFocusedRelationId(null);
  }, [edges, nodeDraft, nodes, pushHistoryAction, setEdges, setNodes]);

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
    const previousEdge = edges.find((edge) => edge.id === edgeDraft.id);
    if (!previousEdge) {
      return;
    }
    const nextProperties = recordFromPairs(edgeDraft.properties);
    const nextEdge: SimpleEdge = {
      ...previousEdge,
      data: {
        relationType: edgeDraft.relationType || "linked",
        properties: nextProperties,
      },
    };
    setEdges((prev) =>
      prev.map((edge) => {
        if (edge.id !== edgeDraft.id) {
          return edge;
        }
        return nextEdge;
      }),
    );
    pushHistoryAction({
      id: createEntityId("history"),
      kind: "update_edge",
      label: `Edited relation ${nextEdge.data?.relationType ?? "linked"}`,
      before: previousEdge,
      after: nextEdge,
    });
    setEdgeDraft(null);
    setEditorState("focus_relation");
    setFocusedRelationId(nextEdge.id);
  }, [edgeDraft, edges, pushHistoryAction, setEdges]);

  const onDiscardEdgeDraft = useCallback(() => {
    setEdgeDraft(null);
    setEditorState("focus_relation");
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

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isEditableTarget =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        Boolean(target?.isContentEditable);

      if (pendingDeleteTarget) {
        if (event.key === "Escape") {
          event.preventDefault();
          setPendingDeleteTarget(null);
        }
        return;
      }

      if (isEditableTarget || editorState === "edit_node" || editorState === "edit_relation") {
        return;
      }

      const modifier = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();

      if (modifier && key === "c") {
        event.preventDefault();
        onCopyFocusedNode();
        return;
      }
      if (modifier && key === "v") {
        event.preventDefault();
        onPasteCopiedNode();
        return;
      }
      if (modifier && key === "z") {
        event.preventDefault();
        onUndo();
        return;
      }
      if (modifier && key === "u") {
        event.preventDefault();
        onRedo();
        return;
      }
      if (key === "delete" || key === "backspace") {
        const canDelete = editorState === "focus" || editorState === "focus_relation";
        if (canDelete) {
          event.preventDefault();
          requestDeleteFocusedSelection();
        }
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    editorState,
    onCopyFocusedNode,
    onPasteCopiedNode,
    onRedo,
    onUndo,
    pendingDeleteTarget,
    requestDeleteFocusedSelection,
  ]);

  const stateLabel = useMemo(() => {
    if (editorState === "browse") {
      return "Browse";
    }
    if (editorState === "focus") {
      return focusedNode ? `Focus: ${(focusedNode.data as SimpleNodeData).name}` : "Focus";
    }
    if (editorState === "focus_relation") {
      return focusedRelation ? `Relation: ${focusedRelation.data?.relationType ?? "linked"}` : "Relation Focus";
    }
    if (editorState === "edit_node") {
      return "Edit Node";
    }
    return "Edit Relation";
  }, [editorState, focusedNode, focusedRelation]);

  const selectedItemLabel = useMemo(() => {
    if (editorState === "focus" && focusedNode) {
      return (focusedNode.data as SimpleNodeData).name;
    }
    if (editorState === "focus_relation" && focusedRelation) {
      const relationType = focusedRelation.data?.relationType ?? "linked";
      const sourceName = nodeNameById.get(focusedRelation.source) ?? focusedRelation.source;
      const targetName = nodeNameById.get(focusedRelation.target) ?? focusedRelation.target;
      return `${relationType}: ${sourceName} -> ${targetName}`;
    }
    return "Nothing selected";
  }, [editorState, focusedNode, focusedRelation, nodeNameById]);

  const onModeBadgeClick = useCallback(() => {
    if (editorState === "edit_node" || editorState === "edit_relation") {
      return;
    }
    onUnfocus();
  }, [editorState, onUnfocus]);

  return (
    <div className="flex h-screen">
      {!readOnly && <aside className={cn(
        "bg-surface border-r border-outline-variant overflow-y-auto transition-all duration-200 shrink-0 flex flex-col gap-3 py-3",
        sidebarOpen ? "w-[280px] px-4" : "w-10 overflow-hidden px-1",
      )}>
        <button type="button" className="w-full text-left font-mono text-[10px] text-on-muted/60 py-1 hover:text-on-muted" onClick={() => setSidebarOpen((prev) => !prev)}>
          {sidebarOpen ? "\u25C0" : "\u25B6"}
        </button>
        {sidebarOpen ? (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 py-1">
              <span className="font-mono text-[10px] text-on-muted border border-outline-variant px-2 py-0.5">{stateLabel}</span>
              <span className={cn("w-2 h-2 rounded-full border", dirty ? "bg-secondary border-secondary" : "bg-surface border-outline-variant")} title={dirty ? "Unsaved" : "Saved"} />
            </div>

            <SidebarSection
              title="Actions"
              open={sectionOpen.actions}
              onToggle={() => setSectionOpen((prev) => ({ ...prev, actions: !prev.actions }))}
            >
              <>
                <div className="flex flex-col gap-0.5 text-[0.8rem]">
                  <strong>Selected</strong>
                  <span>{selectedItemLabel}</span>
                </div>

                {!readOnly && (
                  <div className="flex gap-1 flex-wrap">
                    <button type="button" className="border border-primary bg-primary text-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:bg-primary/90 disabled:opacity-45 disabled:cursor-default" disabled={!dirty} onClick={onSaveWorkspace}>
                      Save workspace
                    </button>
                    <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" disabled={!dirty} onClick={onDiscardWorkspace}>
                      Discard
                    </button>
                  </div>
                )}

                {!readOnly && (
                  <div className="flex gap-1 flex-wrap">
                    <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" onClick={onUndo} disabled={undoStack.length === 0}>
                      Undo
                    </button>
                    <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" onClick={onRedo} disabled={redoStack.length === 0}>
                      Redo
                    </button>
                  </div>
                )}

                <div className="flex gap-1 flex-wrap">
                  <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" onClick={onCopyFocusedNode} disabled={editorState !== "focus"}>
                    Copy
                  </button>
                  <button
                    type="button"
                    className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default"
                    onClick={onPasteCopiedNode}
                    disabled={editorState !== "focus" || !copiedNode}
                  >
                    Paste
                  </button>
                </div>

                <div className="flex gap-1 flex-wrap">
                  <button
                    type="button"
                    className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default"
                    onClick={() => focusedNodeId && openNodeEditor(focusedNodeId)}
                    disabled={editorState !== "focus" || !focusedNodeId}
                  >
                    Edit node
                  </button>
                  <button
                    type="button"
                    className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default"
                    onClick={() => focusedRelationId && openEdgeEditor(focusedRelationId)}
                    disabled={editorState !== "focus_relation" || !focusedRelationId}
                  >
                    Edit relation
                  </button>
                </div>

                <div className="flex gap-1 flex-wrap">
                  <button
                    type="button"
                    className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default"
                    onClick={requestDeleteFocusedSelection}
                    disabled={editorState !== "focus" && editorState !== "focus_relation"}
                  >
                    Delete selected
                  </button>
                </div>

                <div className="font-mono text-[10px] text-on-muted/60 mt-1">Shortcuts: Ctrl/Cmd+C, Ctrl/Cmd+V, Ctrl/Cmd+Z, Ctrl/Cmd+U</div>

                <div className="flex flex-col gap-0.5 text-[0.78rem] text-on-muted">
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

                <div className="flex flex-col gap-1.5">
                  <h3>Relations</h3>
                  {relationTypes.length > 0 ? (
                    relationTypes.map((relationType) => (
                      <label key={relationType} className="flex items-center gap-2 text-[0.8rem] cursor-pointer">
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
                    <p className="font-mono text-[10px] text-on-muted/50 italic">No relation types available.</p>
                  )}
                </div>

                <div className="flex flex-col gap-1.5">
                  <h3>Action history</h3>
                  {undoStack.length === 0 ? (
                    <p className="font-mono text-[10px] text-on-muted/50 italic">No tracked actions yet.</p>
                  ) : (
                    <div className="flex flex-col gap-0.5 max-h-[120px] overflow-y-auto">
                      {undoStack.slice(0, 8).map((action) => (
                        <div key={action.id} className="text-[0.75rem] text-on-muted border-l border-outline-variant pl-2 py-0.5">
                          {action.label}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            </SidebarSection>

            <SidebarSection
              title="Node Filtering"
              open={sectionOpen.filters}
              onToggle={() => setSectionOpen((prev) => ({ ...prev, filters: !prev.filters }))}
            >
              <>
                <div className="flex flex-col gap-1.5">
                  <h3>Filter nodes</h3>
                  <input
                    className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
                    placeholder="Filter by name"
                    value={filterText}
                    onChange={(event) => setFilterText(event.target.value)}
                  />
                  <select
                    className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
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
                    className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
                    placeholder="Property value contains"
                    value={attributeFilterValue}
                    onChange={(event) => setAttributeFilterValue(event.target.value)}
                    disabled={!attributeFilterKey}
                  />
                  <button
                    type="button"
                    className="border border-outline-variant text-on-surface text-[0.7rem] px-1.5 py-0.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default"
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
              </>
            </SidebarSection>

            <SidebarSection
              title="Workspace"
              open={sectionOpen.space}
              onToggle={() => setSectionOpen((prev) => ({ ...prev, space: !prev.space }))}
            >
              <>
                <div className="flex gap-1 flex-wrap">
                  <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" disabled={editorState === "browse"} onClick={onUnfocus}>
                    Unfocus
                  </button>
                  <span className="font-mono text-[10px] text-on-muted/60 mt-1">Edit is on-node</span>
                </div>

                <div className="flex gap-1 flex-wrap">
                  <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" onClick={onLayoutAll}>
                    Layout all
                  </button>
                  <button
                    type="button"
                    className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default"
                    onClick={onLayoutFocusNeighborhood}
                    disabled={!focusedNodeId}
                  >
                    Layout focus
                  </button>
                  <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" onClick={onLayoutCustom} disabled={!customLayoutPositions}>
                    Layout custom
                  </button>
                </div>

                <div className="flex flex-col gap-1.5">
                  <h3>View options</h3>
                  <label className="flex items-center gap-2 text-[0.8rem] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={hideNonNeighbors}
                      onChange={(event) => setHideNonNeighbors(event.target.checked)}
                    />
                    Hide non-neighbors
                  </label>
                </div>
              </>
            </SidebarSection>

            <SidebarSection
              title="Creation"
              open={sectionOpen.creation}
              onToggle={() => setSectionOpen((prev) => ({ ...prev, creation: !prev.creation }))}
            >
              <>
                <div className="flex gap-1 flex-wrap">
                  <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45 disabled:cursor-default" onClick={onAddNode}>
                    + Add node
                  </button>
                </div>

                <div className="flex flex-col gap-1.5">
                  <h3>Drag palette</h3>
                  <div className="flex flex-wrap gap-1">
                    {NODE_TEMPLATES.map((template) => (
                      <button
                        key={template.name}
                        type="button"
                        draggable
                        className="bg-surface border border-outline-variant text-on-surface text-[0.78rem] px-2 py-0.5 cursor-grab hover:border-primary active:cursor-grabbing"
                        onDragStart={(event) => onTemplateDragStart(event, template)}
                      >
                        + {template.name}
                      </button>
                    ))}
                  </div>
                  <p className="font-mono text-[10px] text-on-muted/50 mt-1">Drag a template into the canvas to create a node.</p>
                </div>
              </>
            </SidebarSection>

            <SidebarSection
              title="Vacant Nodes"
              open={sectionOpen.vacant}
              onToggle={() => setSectionOpen((prev) => ({ ...prev, vacant: !prev.vacant }))}
            >
              <>
                {inFocusModes && hideNonNeighbors ? (
                  <p className="font-mono text-[10px] text-on-muted/50 italic">Hidden non-neighbors can still be linked from this drawer.</p>
                ) : null}
                {!focusedNodeId ? (
                  <p className="font-mono text-[10px] text-on-muted/50 italic">Focus a node to see candidate connection targets.</p>
                ) : hiddenRelationTypes.includes("linked") ? (
                  <p className="font-mono text-[10px] text-on-muted/50 italic">Enable relation type `linked` to create new node-to-node links.</p>
                ) : vacantCandidateNodes.length === 0 ? (
                  <p className="font-mono text-[10px] text-on-muted/50 italic">No vacant candidates under current filters.</p>
                ) : (
                  !readOnly && (
                    <div className="flex flex-col gap-0.5 max-h-[200px] overflow-y-auto">
                      {vacantCandidateNodes.map((node) => (
                        <button
                          key={node.id}
                          type="button"
                          className="text-left px-2 py-1 text-[0.8rem] text-on-surface hover:bg-primary/10 hover:text-primary"
                          onClick={() => onConnectFromVacantDrawer(node.id)}
                        >
                          {(node.data as SimpleNodeData).name}
                        </button>
                      ))}
                    </div>
                  )
                )}
              </>
            </SidebarSection>
          </div>
        ) : null}
      </aside>}

      <div className="flex-1 relative" ref={canvasRef}>
        <ReactFlow<SimpleNode, SimpleEdge>
          onDrop={onDropOnCanvas}
          onDragOver={onDragOverCanvas}
          nodes={displayNodes}
          edges={displayEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={readOnly ? () => {} : onConnect}
          onConnectStart={readOnly ? () => {} : onConnectStart}
          onConnectEnd={readOnly ? () => {} : onConnectEnd}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          connectionMode={ConnectionMode.Loose}
          deleteKeyCode={null}
          minZoom={0.1}
          fitView
          attributionPosition="bottom-left"
          nodesDraggable={!readOnly}
          nodesConnectable={!readOnly}
        >
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => CATEGORY_COLORS[(node.data as SimpleNodeData)?.category]?.bg ?? "#1e2022"}
            style={{ background: '#0d0f10', border: '1px solid rgba(255,255,255,0.08)' }}
            maskColor="rgba(0,0,0,0.4)"
          />
          <Controls style={{ background: '#0d0f10', border: '1px solid rgba(255,255,255,0.08)' }} />
          <Background gap={20} size={1} />
        </ReactFlow>
        <button
          type="button"
          className="absolute bottom-3 right-3 z-50 font-mono text-[10px] border border-outline-variant px-2 py-1 text-on-muted bg-surface/80 hover:text-on-surface disabled:opacity-50 disabled:cursor-default"
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
          <div className="absolute z-50 bg-surface border border-outline-variant p-3 flex flex-col gap-2 shadow-xl min-w-[200px]" style={{ left: connectMenu.x, top: connectMenu.y }}>
            <h4>Connect from {connectMenu.sourceNodeId}</h4>
            <button type="button" className="border border-outline-variant text-on-surface text-[0.7rem] px-1.5 py-0.5 cursor-pointer hover:border-primary bg-transparent disabled:opacity-45" onClick={onCreateAndConnectNode}>
              + Create new and connect
            </button>
            <div className="flex flex-col gap-0.5 max-h-[200px] overflow-y-auto">
              {connectCandidates.map((node) => (
                <button
                  key={node.id}
                  type="button"
                  className="text-left px-2 py-1 text-[0.8rem] text-on-surface hover:bg-primary/10 hover:text-primary"
                  onClick={() => onConnectToExistingNode(node.id)}
                >
                  {(node.data as SimpleNodeData).name}
                </button>
              ))}
            </div>
            <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent" onClick={() => setConnectMenu(null)}>
              Cancel
            </button>
          </div>
        ) : null}
      </div>

      {pendingDeleteTarget ? (
        <div className="fixed inset-0 bg-slate-900/35 backdrop-blur-[2px] flex items-center justify-center z-50">
          <div className="bg-surface border border-outline-variant p-6 flex flex-col gap-4 w-[360px] max-h-[90vh] overflow-y-auto">
            <h2>{pendingDeleteTarget.title}</h2>
            <p className="text-[0.88rem] text-on-muted">{pendingDeleteTarget.description}</p>
            <div className="flex gap-2 justify-end">
              <button type="button" className="border border-error text-error text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:bg-error/10 bg-transparent" onClick={onConfirmDeleteSelection}>
                Delete
              </button>
              <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent" onClick={() => setPendingDeleteTarget(null)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {readOnly && editorState === "edit_node" && focusedNode ? (
        <div
          className="fixed inset-0 bg-slate-900/35 backdrop-blur-[2px] flex items-center justify-center z-50"
          onClick={() => setEditorState("browse")}
        >
          <div
            className="bg-surface border border-outline-variant p-6 flex flex-col gap-4 w-[500px] max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-on-surface font-mono text-sm">{(focusedNode.data as SimpleNodeData).name}</h2>
              <button
                type="button"
                className="text-on-muted hover:text-on-surface font-mono text-xs px-2 py-1 border border-outline-variant bg-transparent"
                onClick={() => setEditorState("browse")}
              >
                ✕
              </button>
            </div>
            {(() => {
              const metaRecord = (focusedNode.data as SimpleNodeData).meta as Record<string, unknown> | undefined;
              const schemaType = metaRecord?.['schemaType'] as { attributes?: { name: string; type: string; required: boolean; values?: string[]; note?: string }[] } | undefined;
              const attrs = schemaType?.attributes ?? [];
              return attrs.length > 0 ? (
                <div className="flex flex-col gap-1">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-on-muted mb-1">Attributes</span>
                  {attrs.map((attr) => (
                    <div key={attr.name} className="flex items-start gap-2 font-mono text-[11px]">
                      <span className="text-primary w-36 shrink-0">{attr.name}</span>
                      <span className="text-on-muted">{attr.type}</span>
                      {attr.required && <span className="text-error/70 ml-auto">required</span>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="font-mono text-[10px] text-on-muted/50 italic">No attributes defined.</p>
              );
            })()}
          </div>
        </div>
      ) : null}

      {!readOnly && editorState === "edit_node" && nodeDraft ? (
        <div className="fixed inset-0 bg-slate-900/35 backdrop-blur-[2px] flex items-center justify-center z-50">
          <div className="bg-surface border border-outline-variant p-6 flex flex-col gap-4 w-[500px] max-h-[90vh] overflow-y-auto">
            <h2>Edit node</h2>
            <label className="flex flex-col gap-1 text-[0.83rem]">
              <span>Name</span>
              <input
                className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
                value={nodeDraft.name}
                onChange={(event) => setNodeDraft((prev) => (prev ? { ...prev, name: event.target.value } : prev))}
              />
            </label>
            <label className="flex flex-col gap-1 text-[0.83rem]">
              <span>Category</span>
              <select
                className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
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

            <div className="flex flex-col gap-1 text-[0.83rem]">
              <span>Relations</span>
              <div className="flex flex-col gap-1 max-h-[120px] overflow-y-auto">
                {nodeRelationPills.length > 0 ? (
                  nodeRelationPills.map((pill) => (
                    <div key={pill.id} className="flex items-center gap-1">
                      <span className="text-[0.78rem] text-on-muted flex-1">{pill.text}</span>
                      <button
                        type="button"
                        className="text-error text-[0.8rem] hover:text-error/80 px-1 py-0.5"
                        title="Remove relation"
                        onClick={() => onRemoveRelationFromNodeModal(pill.id)}
                      >
                        x
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="font-mono text-[10px] text-on-muted/50 italic">No relations for this node yet.</p>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-1 text-[0.83rem]">
              <span>Properties</span>
              <div className="flex flex-col gap-1">
                {nodeDraft.properties.map((pair, index) => (
                  <div key={`${index}-${pair.key}`} className="flex gap-1 items-start">
                    <input
                      className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
                      placeholder="key"
                      value={pair.key}
                      onChange={(event) => onUpdateNodeDraftProperty(index, "key", event.target.value)}
                    />
                    <select
                      className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
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
                    <button type="button" className="text-error text-[0.8rem] hover:text-error/80 px-1 py-0.5" onClick={() => onRemoveNodeDraftProperty(index)}>
                      x
                    </button>
                  </div>
                ))}
              </div>
              <button type="button" className="border border-outline-variant text-on-surface text-[0.7rem] px-1.5 py-0.5 cursor-pointer hover:border-primary bg-transparent" onClick={onAddNodeDraftProperty}>
                + Add property
              </button>
            </div>

            <div className="flex gap-2 justify-end">
              <button type="button" className="border border-primary bg-primary text-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:bg-primary/90" onClick={onSaveNodeDraft}>
                Save node
              </button>
              <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent" onClick={onDiscardNodeDraft}>
                Discard
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {!readOnly && editorState === "edit_relation" && edgeDraft ? (
        <div className="fixed inset-0 bg-slate-900/35 backdrop-blur-[2px] flex items-center justify-center z-50">
          <div className="bg-surface border border-outline-variant p-6 flex flex-col gap-4 w-[500px] max-h-[90vh] overflow-y-auto">
            <h2>Edit relation</h2>
            <label className="flex flex-col gap-1 text-[0.83rem]">
              <span>Type</span>
              <input
                className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
                value={edgeDraft.relationType}
                onChange={(event) =>
                  setEdgeDraft((prev) => (prev ? { ...prev, relationType: event.target.value } : prev))
                }
              />
            </label>

            <div className="flex flex-col gap-1 text-[0.83rem]">
              <span>Relation properties</span>
              <div className="flex flex-col gap-1">
                {edgeDraft.properties.map((pair, index) => (
                  <div key={`${index}-${pair.key}`} className="flex gap-1 items-start">
                    <input
                      className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
                      placeholder="key"
                      value={pair.key}
                      onChange={(event) => onUpdateEdgeDraftProperty(index, "key", event.target.value)}
                    />
                    <select
                      className="border border-outline-variant bg-surface-low text-on-surface text-[0.78rem] px-2 py-1 w-full"
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
                    <button type="button" className="text-error text-[0.8rem] hover:text-error/80 px-1 py-0.5" onClick={() => onRemoveEdgeDraftProperty(index)}>
                      x
                    </button>
                  </div>
                ))}
              </div>
              <button type="button" className="border border-outline-variant text-on-surface text-[0.7rem] px-1.5 py-0.5 cursor-pointer hover:border-primary bg-transparent" onClick={onAddEdgeDraftProperty}>
                + Add property
              </button>
            </div>

            <div className="flex gap-2 justify-end">
              <button type="button" className="border border-primary bg-primary text-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:bg-primary/90" onClick={onSaveEdgeDraft}>
                Save relation
              </button>
              <button type="button" className="border border-outline-variant text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer hover:border-primary bg-transparent" onClick={onDiscardEdgeDraft}>
                Discard
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function KnowledgeGraph(props: KnowledgeGraphProps): JSX.Element {
  return (
    <section className="m-0 min-h-screen">
      <ReactFlowProvider>
        <NodeEditorInner {...props} />
      </ReactFlowProvider>
    </section>
  );
}
