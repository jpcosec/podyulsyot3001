import { useCallback, useMemo, type MouseEvent } from 'react';

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { registry } from '@/schema/registry';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';
import type { ASTEdge, ASTNode } from '@/stores/types';

import { GroupShell } from './GroupShell';
import { NodeShell } from './NodeShell';
import { ButtonEdge, FloatingEdge } from './edges';
import { useKeyboard } from './hooks';
import { EdgeInspector, NodeInspector } from './panels';
import { CanvasSidebar } from './sidebar';

type CanvasNode = Node<ASTNode['data'], string>;
type CanvasEdgeData = NonNullable<ASTEdge['data']>;
type CanvasEdge = Edge<CanvasEdgeData, string>;

const nodeTypes = {
  node: NodeShell,
  group: GroupShell,
};

const edgeTypes = {
  floating: FloatingEdge,
  button: ButtonEdge,
};

function asCanvasNode(node: ASTNode): CanvasNode {
  return {
    ...node,
    type: node.type === 'group' ? 'group' : 'node',
  };
}

function asCanvasEdge(edge: ASTEdge): CanvasEdge {
  return {
    ...edge,
    data: edge.data ?? { relationType: 'linked', properties: {} },
    type: edge.type === 'button' ? 'button' : 'floating',
  };
}

export function getNodeTitle(node: ASTNode): string {
  const payloadValue = node.data.payload.value;
  if (payloadValue && typeof payloadValue === 'object') {
    const candidate = payloadValue as Record<string, unknown>;
    const title = candidate.name ?? candidate.title;
    if (typeof title === 'string' && title.trim().length > 0) {
      return title;
    }
  }

  return node.id;
}

export function shouldHideForTextFilter(node: ASTNode, filterText: string): boolean {
  if (!filterText) {
    return false;
  }

  return !getNodeTitle(node).toLowerCase().includes(filterText.toLowerCase());
}

export function buildDisplayNodes(nodes: ASTNode[], filterText: string): CanvasNode[] {
  return nodes.map((node) =>
    asCanvasNode({
      ...node,
      hidden: Boolean(node.hidden) || shouldHideForTextFilter(node, filterText),
    }),
  );
}

function toConnectionEdge(connection: Connection): ASTEdge | null {
  if (!connection.source || !connection.target) {
    return null;
  }

  return {
    id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
    source: connection.source,
    target: connection.target,
    type: 'floating',
    data: {
      relationType: 'linked',
      properties: {},
    },
  };
}

export function GraphCanvas() {
  useKeyboard();

  const nodes = useGraphStore((state) => state.nodes);
  const edges = useGraphStore((state) => state.edges);
  const updateNode = useGraphStore((state) => state.updateNode);
  const updateEdge = useGraphStore((state) => state.updateEdge);
  const addElements = useGraphStore((state) => state.addElements);
  const removeElements = useGraphStore((state) => state.removeElements);

  const filters = useUIStore((state) => state.filters);
  const setFocusedNode = useUIStore((state) => state.setFocusedNode);
  const setFocusedEdge = useUIStore((state) => state.setFocusedEdge);
  const setEditorState = useUIStore((state) => state.setEditorState);

  const isValidConnection = useCallback(
    (connectionOrEdge: Connection | CanvasEdge): boolean => {
      const sourceId = connectionOrEdge.source;
      const targetId = connectionOrEdge.target;

      if (!sourceId || !targetId) {
        return false;
      }

      const source = nodes.find((node) => node.id === sourceId);
      const target = nodes.find((node) => node.id === targetId);
      if (!source || !target) {
        return false;
      }

      return registry.canConnect(source.data.typeId, target.data.typeId);
    },
    [nodes],
  );

  const onNodesChange = useCallback(
    (changes: NodeChange<CanvasNode>[]) => {
      for (const change of changes) {
        if (change.type === 'position' && change.position) {
          updateNode(
            change.id,
            { position: change.position },
            { isVisualOnly: Boolean(change.dragging) },
          );
          continue;
        }

        if (change.type === 'select') {
          updateNode(change.id, { selected: change.selected }, { isVisualOnly: true });
        }
      }
    },
    [updateNode],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange<CanvasEdge>[]) => {
      for (const change of changes) {
        if (change.type === 'select') {
          updateEdge(change.id, { selected: change.selected }, { isVisualOnly: true });
        }
      }
    },
    [updateEdge],
  );

  const onNodesDelete = useCallback(
    (deletedNodes: CanvasNode[]) => {
      const deletedNodeIds = deletedNodes.map((node) => node.id);
      const deletedNodeIdSet = new Set(deletedNodeIds);

      const connectedEdgeIds = edges
        .filter((edge) => deletedNodeIdSet.has(edge.source) || deletedNodeIdSet.has(edge.target))
        .map((edge) => edge.id);

      removeElements(deletedNodeIds, connectedEdgeIds);
    },
    [edges, removeElements],
  );

  const onEdgesDelete = useCallback(
    (deletedEdges: CanvasEdge[]) => {
      removeElements(
        [],
        deletedEdges.map((edge) => edge.id),
      );
    },
    [removeElements],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const edge = toConnectionEdge(connection);
      if (!edge) {
        return;
      }

      addElements([], [edge]);
    },
    [addElements],
  );

  const onNodeClick = useCallback(
    (_event: MouseEvent, node: CanvasNode) => {
      setFocusedEdge(null);
      setFocusedNode(node.id);
      setEditorState('edit_node');
    },
    [setEditorState, setFocusedEdge, setFocusedNode],
  );

  const onEdgeClick = useCallback(
    (_event: MouseEvent, edge: CanvasEdge) => {
      setFocusedNode(null);
      setFocusedEdge(edge.id);
      setEditorState('edit_relation');
    },
    [setEditorState, setFocusedEdge, setFocusedNode],
  );

  const onPaneClick = useCallback(() => {
    setFocusedNode(null);
    setFocusedEdge(null);
    setEditorState('browse');
  }, [setEditorState, setFocusedEdge, setFocusedNode]);

  const displayNodes = useMemo(() => {
    return buildDisplayNodes(nodes, filters.filterText);
  }, [nodes, filters.filterText]);

  const displayEdges = useMemo(() => {
    const hiddenNodeIds = new Set(
      displayNodes.filter((node) => node.hidden).map((node) => node.id),
    );

    return edges
      .filter((edge) => {
        const relationType = edge.data?.relationType ?? '';
        if (filters.hiddenRelationTypes.includes(relationType)) {
          return false;
        }

        if (hiddenNodeIds.has(edge.source) || hiddenNodeIds.has(edge.target)) {
          return false;
        }

        return true;
      })
      .map(asCanvasEdge);
  }, [edges, displayNodes, filters.hiddenRelationTypes]);

  return (
    <div className="flex h-full w-full">
      <div className="h-full flex-1">
        <ReactFlow
          nodes={displayNodes}
          edges={displayEdges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          isValidConnection={isValidConnection}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodesDelete={onNodesDelete}
          onEdgesDelete={onEdgesDelete}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          defaultEdgeOptions={{ type: 'floating' }}
        >
          <Background color="#e5e7eb" gap={16} />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(node) => {
              const typeId = node.data?.typeId;
              return typeId ? `var(--token-${typeId}, #888)` : '#888';
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
          />
        </ReactFlow>
      </div>
      <CanvasSidebar />
      <NodeInspector />
      <EdgeInspector />
    </div>
  );
}
