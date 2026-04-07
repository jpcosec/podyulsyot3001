import { useEffect, useState } from 'react';
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
import './xy-theme.css';

import { registry } from '@/schema/registry';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';
import type { ASTEdge, ASTNode } from '@/stores/types';

import { GroupShell } from './GroupShell';
import { NodeShell } from './NodeShell';
import { ButtonEdge, FloatingEdge } from './edges';

type CanvasNode = Node<ASTNode['data'], string>;
type CanvasEdgeData = NonNullable<ASTEdge['data']>;
type CanvasEdge = Edge<CanvasEdgeData, string>;

const nodeTypes = {
  default: NodeShell,
  group: GroupShell,
};

const edgeTypes = {
  floating: FloatingEdge,
  button: ButtonEdge,
};

function asCanvasNode(node: ASTNode): CanvasNode {
  return {
    id: node.id,
    type: node.type === 'group' ? 'group' : 'default',
    position: node.position,
    data: node.data,
    parentId: node.parentId,
    extent: node.extent as 'parent' | undefined,
    style: node.style,
    hidden: node.hidden,
    selected: node.selected,
  };
}

function asCanvasEdge(edge: ASTEdge): CanvasEdge {
  return {
    ...edge,
    data: edge.data ?? { relationType: 'linked', properties: {} },
    type: edge.type === 'button' ? 'button' : 'floating',
  };
}

export function GraphCanvas() {
  const nodes = useGraphStore((state) => state.nodes);
  const edges = useGraphStore((state) => state.edges);
  const onNodesChange = useGraphStore((state) => state.onNodesChange);
  const onEdgesChange = useGraphStore((state) => state.onEdgesChange);
  const onConnect = useGraphStore((state) => state.onConnect);
  const selectedNode = useUIStore((state) => state.selectedNode);
  const selectedEdge = useUIStore((state) => state.selectedEdge);

  const [nodesState, setNodesState] = useState<CanvasNode[]>([]);
  const [edgesState, setEdgesState] = useState<CanvasEdge[]>([]);

  useEffect(() => {
    setNodesState(nodes.map(asCanvasNode));
  }, [nodes]);

  useEffect(() => {
    setEdgesState(edges.map(asCanvasEdge));
  }, [edges]);

  return (
    <ReactFlow
      nodes={nodesState}
      edges={edgesState}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.1}
      maxZoom={2}
      defaultEdgeOptions={{ type: 'floating' }}
      proOptions={{ hideAttribution: true }}
    >
      <Background gap={20} size={1} color="rgba(148, 163, 184, 0.18)" />
      <Controls showInteractive={false} />
      <MiniMap
        nodeColor={(node) => (node.selected ? '#00f2ff' : '#94a3b8')}
        maskColor="rgba(2, 6, 23, 0.55)"
        pannable
        zoomable
      />
    </ReactFlow>
  );
}
