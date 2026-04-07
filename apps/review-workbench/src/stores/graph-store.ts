import { create } from 'zustand';

import type { ASTEdge, ASTNode, SemanticAction } from './types';
import type { Connection, EdgeChange, NodeChange } from '@xyflow/react';

type GraphSnapshot = { nodes: ASTNode[]; edges: ASTEdge[] };
type UpdateOptions = { isVisualOnly?: boolean };

interface CreateElementsPayload {
  nodes: ASTNode[];
  edges: ASTEdge[];
}

interface UpdateNodePayload {
  before: ASTNode;
  after: ASTNode;
}

interface UpdateEdgePayload {
  before: ASTEdge;
  after: ASTEdge;
}

export interface GraphStore {
  nodes: ASTNode[];
  edges: ASTEdge[];
  undoStack: SemanticAction[];
  redoStack: SemanticAction[];
  savedSnapshot: string | null;

  isDirty: () => boolean;

  addElements: (nodes: ASTNode[], edges: ASTEdge[]) => void;
  removeElements: (nodeIds: string[], edgeIds: string[]) => void;
  updateNode: (nodeId: string, patch: Partial<ASTNode>, options?: UpdateOptions) => void;
  updateEdge: (edgeId: string, patch: Partial<ASTEdge>, options?: UpdateOptions) => void;

  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;

  undo: () => void;
  redo: () => void;

  loadGraph: (nodes: ASTNode[], edges: ASTEdge[]) => void;
  markSaved: () => void;
}

function snapshot(nodes: ASTNode[], edges: ASTEdge[]): string {
  return JSON.stringify({ nodes, edges });
}

function upsertById<T extends { id: string }>(existing: T[], items: T[]): T[] {
  const index = new Map(existing.map((item, idx) => [item.id, idx]));
  const next = [...existing];

  for (const item of items) {
    const idx = index.get(item.id);
    if (idx === undefined) {
      next.push(item);
      continue;
    }
    next[idx] = item;
  }

  return next;
}

function withoutIds<T extends { id: string }>(items: T[], ids: string[]): T[] {
  const blocked = new Set(ids);
  return items.filter((item) => !blocked.has(item.id));
}

function mergeNode(node: ASTNode, patch: Partial<ASTNode>): ASTNode {
  const replacesProperties = Boolean(
    patch.data && Object.prototype.hasOwnProperty.call(patch.data, 'properties'),
  );

  return {
    ...node,
    ...patch,
    position: {
      ...node.position,
      ...(patch.position ?? {}),
    },
    data: {
      ...node.data,
      ...(patch.data ?? {}),
      payload: node.data.payload ? {
        ...node.data.payload,
        ...(patch.data?.payload ?? {}),
      } : patch.data?.payload,
      properties: replacesProperties ? (patch.data?.properties ?? {}) : (node.data.properties ?? {}),
    },
  };
}

function mergeEdge(edge: ASTEdge, patch: Partial<ASTEdge>): ASTEdge {
  const dataPatch = patch.data;

  const readPatchedMetadata = (
    key: '_originalSource' | '_originalTarget' | '_originalRelationType',
  ): string | undefined => {
    if (!dataPatch) {
      return edge.data?.[key];
    }

    if (Object.prototype.hasOwnProperty.call(dataPatch, key)) {
      return dataPatch[key];
    }

    return edge.data?.[key];
  };

  const nextData = patch.data
    ? {
        relationType: patch.data.relationType ?? edge.data?.relationType ?? 'linked',
        properties: {
          ...(edge.data?.properties ?? {}),
          ...(patch.data.properties ?? {}),
        },
        _originalSource: readPatchedMetadata('_originalSource'),
        _originalTarget: readPatchedMetadata('_originalTarget'),
        _originalRelationType: readPatchedMetadata('_originalRelationType'),
      }
    : edge.data;

  return {
    ...edge,
    ...patch,
    data: nextData,
  };
}

function applyUndoAction(state: GraphSnapshot, action: SemanticAction): GraphSnapshot {
  switch (action.type) {
    case 'CREATE_ELEMENTS': {
      const payload = action.payload as CreateElementsPayload;
      return {
        nodes: withoutIds(state.nodes, payload.nodes.map((node) => node.id)),
        edges: withoutIds(state.edges, payload.edges.map((edge) => edge.id)),
      };
    }
    case 'DELETE_ELEMENTS': {
      const payload = action.payload as CreateElementsPayload;
      return {
        nodes: upsertById(state.nodes, payload.nodes),
        edges: upsertById(state.edges, payload.edges),
      };
    }
    case 'UPDATE_NODE': {
      const payload = action.payload as UpdateNodePayload;
      return {
        ...state,
        nodes: state.nodes.map((node) => (node.id === payload.before.id ? payload.before : node)),
      };
    }
    case 'UPDATE_EDGE': {
      const payload = action.payload as UpdateEdgePayload;
      return {
        ...state,
        edges: state.edges.map((edge) => (edge.id === payload.before.id ? payload.before : edge)),
      };
    }
  }
}

function applyRedoAction(state: GraphSnapshot, action: SemanticAction): GraphSnapshot {
  switch (action.type) {
    case 'CREATE_ELEMENTS': {
      const payload = action.payload as CreateElementsPayload;
      return {
        nodes: upsertById(state.nodes, payload.nodes),
        edges: upsertById(state.edges, payload.edges),
      };
    }
    case 'DELETE_ELEMENTS': {
      const payload = action.payload as CreateElementsPayload;
      return {
        nodes: withoutIds(state.nodes, payload.nodes.map((node) => node.id)),
        edges: withoutIds(state.edges, payload.edges.map((edge) => edge.id)),
      };
    }
    case 'UPDATE_NODE': {
      const payload = action.payload as UpdateNodePayload;
      return {
        ...state,
        nodes: state.nodes.map((node) => (node.id === payload.after.id ? payload.after : node)),
      };
    }
    case 'UPDATE_EDGE': {
      const payload = action.payload as UpdateEdgePayload;
      return {
        ...state,
        edges: state.edges.map((edge) => (edge.id === payload.after.id ? payload.after : edge)),
      };
    }
  }
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  nodes: [],
  edges: [],
  undoStack: [],
  redoStack: [],
  savedSnapshot: null,

  isDirty: () => {
    const { nodes, edges, savedSnapshot } = get();
    return snapshot(nodes, edges) !== savedSnapshot;
  },

  addElements: (nodes, edges) => {
    const action: SemanticAction = {
      type: 'CREATE_ELEMENTS',
      payload: { nodes, edges },
      timestamp: Date.now(),
      affectedIds: [...nodes.map((node) => node.id), ...edges.map((edge) => edge.id)],
    };

    set((state) => ({
      nodes: upsertById(state.nodes, nodes),
      edges: upsertById(state.edges, edges),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },

  removeElements: (nodeIds, edgeIds) => {
    const current = get();
    const nodeIdSet = new Set(nodeIds);
    const edgeIdSet = new Set(edgeIds);

    const nodesToRemove = current.nodes.filter((node) => nodeIdSet.has(node.id));
    const edgesToRemove = current.edges.filter((edge) =>
      edgeIdSet.has(edge.id) || nodeIdSet.has(edge.source) || nodeIdSet.has(edge.target),
    );

    if (nodesToRemove.length === 0 && edgesToRemove.length === 0) {
      return;
    }

    const action: SemanticAction = {
      type: 'DELETE_ELEMENTS',
      payload: { nodes: nodesToRemove, edges: edgesToRemove },
      timestamp: Date.now(),
      affectedIds: [...nodesToRemove.map((node) => node.id), ...edgesToRemove.map((edge) => edge.id)],
    };

    set((state) => ({
      nodes: withoutIds(state.nodes, nodesToRemove.map((node) => node.id)),
      edges: withoutIds(state.edges, edgesToRemove.map((edge) => edge.id)),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },

  updateNode: (nodeId, patch, options) => {
    const existing = get().nodes.find((node) => node.id === nodeId);
    if (!existing) {
      return;
    }

    const nextNode = mergeNode(existing, patch);
    if (JSON.stringify(existing) === JSON.stringify(nextNode)) {
      return;
    }

    if (options?.isVisualOnly) {
      set((state) => ({
        nodes: state.nodes.map((node) => (node.id === nodeId ? nextNode : node)),
      }));
      return;
    }

    const action: SemanticAction = {
      type: 'UPDATE_NODE',
      payload: { before: existing, after: nextNode },
      timestamp: Date.now(),
      affectedIds: [nodeId],
    };

    set((state) => ({
      nodes: state.nodes.map((node) => (node.id === nodeId ? nextNode : node)),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },

  updateEdge: (edgeId, patch, options) => {
    const existing = get().edges.find((edge) => edge.id === edgeId);
    if (!existing) {
      return;
    }

    const nextEdge = mergeEdge(existing, patch);
    if (JSON.stringify(existing) === JSON.stringify(nextEdge)) {
      return;
    }

    if (options?.isVisualOnly) {
      set((state) => ({
        edges: state.edges.map((edge) => (edge.id === edgeId ? nextEdge : edge)),
      }));
      return;
    }

    const action: SemanticAction = {
      type: 'UPDATE_EDGE',
      payload: { before: existing, after: nextEdge },
      timestamp: Date.now(),
      affectedIds: [edgeId],
    };

    set((state) => ({
      edges: state.edges.map((edge) => (edge.id === edgeId ? nextEdge : edge)),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },

  onNodesChange: (changes) => {
    for (const change of changes) {
      if (change.type === 'position' && change.position) {
        get().updateNode(change.id, { position: change.position }, { isVisualOnly: Boolean(change.dragging) });
        continue;
      }

      if (change.type === 'select') {
        get().updateNode(change.id, { selected: change.selected }, { isVisualOnly: true });
      }
    }
  },

  onEdgesChange: (changes) => {
    for (const change of changes) {
      if (change.type === 'select') {
        get().updateEdge(change.id, { selected: change.selected }, { isVisualOnly: true });
      }
    }
  },

  onConnect: (connection) => {
    if (!connection.source || !connection.target) {
      return;
    }

    const newEdge: ASTEdge = {
      id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
      source: connection.source,
      target: connection.target,
      type: 'floating',
      data: {
        relationType: 'linked',
        properties: {},
      },
    };

    get().addElements([], [newEdge]);
  },

  undo: () => {
    const { undoStack, redoStack, nodes, edges } = get();
    const action = undoStack[0];

    if (!action) {
      return;
    }

    const nextState = applyUndoAction({ nodes, edges }, action);
    set({
      ...nextState,
      undoStack: undoStack.slice(1),
      redoStack: [action, ...redoStack],
    });
  },

  redo: () => {
    const { redoStack, undoStack, nodes, edges } = get();
    const action = redoStack[0];

    if (!action) {
      return;
    }

    const nextState = applyRedoAction({ nodes, edges }, action);
    set({
      ...nextState,
      undoStack: [action, ...undoStack],
      redoStack: redoStack.slice(1),
    });
  },

  loadGraph: (nodes, edges) => {
    set({
      nodes,
      edges,
      undoStack: [],
      redoStack: [],
      savedSnapshot: snapshot(nodes, edges),
    });
  },

  markSaved: () => {
    const { nodes, edges } = get();
    set({ savedSnapshot: snapshot(nodes, edges) });
  },
}));
