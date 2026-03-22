import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import { EntryNode } from './EntryNode';
import { SkillNode } from './SkillNode';
import type { CvEntry, CvSkill, CvDemonstratesEdge } from '../../../types/api.types';

const ENTRY_WIDTH  = 280;
const ENTRY_HEIGHT = 80;
const SKILL_WIDTH  = 160;
const SKILL_HEIGHT = 50;

const nodeTypes = {
  entry: EntryNode,
  skill: SkillNode,
};

function layoutWithDagre(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 30, ranksep: 100 });

  nodes.forEach(node => {
    const w = node.type === 'entry' ? ENTRY_WIDTH : SKILL_WIDTH;
    const h = node.type === 'entry' ? ENTRY_HEIGHT : SKILL_HEIGHT;
    g.setNode(node.id, { width: w, height: h });
  });
  edges.forEach(edge => g.setEdge(edge.source, edge.target));

  dagre.layout(g);

  return nodes.map(node => {
    const pos = g.node(node.id);
    const w = node.type === 'entry' ? ENTRY_WIDTH : SKILL_WIDTH;
    const h = node.type === 'entry' ? ENTRY_HEIGHT : SKILL_HEIGHT;
    return { ...node, position: { x: pos.x - w / 2, y: pos.y - h / 2 } };
  });
}

interface Props {
  entries: CvEntry[];
  skills: CvSkill[];
  demonstrates: CvDemonstratesEdge[];
  selectedNodeId: string | null;
  onNodeClick: (id: string, type: 'entry' | 'skill') => void;
}

export function CvGraphCanvas({ entries, skills, demonstrates, selectedNodeId, onNodeClick }: Props) {
  const initialNodes: Node[] = useMemo(() => [
    ...entries.map(entry => ({
      id: entry.id,
      type: 'entry' as const,
      position: { x: 0, y: 0 },
      data: { entry, selected: entry.id === selectedNodeId },
    })),
    ...skills.map(skill => ({
      id: skill.id,
      type: 'skill' as const,
      position: { x: 0, y: 0 },
      data: { skill, selected: skill.id === selectedNodeId },
    })),
  ], [entries, skills, selectedNodeId]);

  const initialEdges: Edge[] = useMemo(() => demonstrates.map(d => {
    const sourceEntry = entries.find(e => e.id === d.source);
    return {
      id: d.id,
      source: d.source,
      target: d.target,
      type: 'default',
      style: {
        stroke: '#00f2ff',
        strokeDasharray: '6 3',
      },
      animated: sourceEntry?.essential ?? false,
    };
  }), [demonstrates, entries]);

  const laidOutNodes = useMemo(
    () => layoutWithDagre(initialNodes, initialEdges),
    [initialNodes, initialEdges]
  );

  const [nodes, , onNodesChange] = useNodesState(laidOutNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const type = node.type === 'entry' ? 'entry' : 'skill';
    onNodeClick(node.id, type);
  }, [onNodeClick]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      onNodeClick={handleNodeClick}
      fitView
      className="bg-background"
    >
      <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="rgba(0,242,255,0.05)" />
      <Controls className="!bg-surface-container !border-outline/20 !shadow-none" />
    </ReactFlow>
  );
}
