import { useCallback } from 'react';

import dagre from 'dagre';

import { useGraphStore } from '@/stores/graph-store';

export interface LayoutOptions {
  direction?: 'LR' | 'TB' | 'RL' | 'BT';
  nodeSpacing?: number;
  rankSpacing?: number;
}

type LayoutResult = Array<{ id: string; position: { x: number; y: number } }>;

type UpdateNode = (
  id: string,
  updates: { position: { x: number; y: number } },
  options: { isVisualOnly: true },
) => void;

export interface UseGraphLayoutResult {
  layout: (options?: LayoutOptions) => LayoutResult;
}

function getLayoutedElements(
  nodes: Array<{ id: string; width?: number; height?: number }>,
  edges: Array<{ id: string; source: string; target: string }>,
  options: LayoutOptions,
): LayoutResult {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const direction = options.direction ?? 'LR';
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: options.nodeSpacing ?? 50,
    ranksep: options.rankSpacing ?? 100,
    marginx: 0,
    marginy: 0,
  });

  const nodeWidth = 200;
  const nodeHeight = 80;

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: node.width ?? nodeWidth, height: node.height ?? nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const result: LayoutResult = nodes
    .map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      if (!nodeWithPosition) return null;

      const { x, y } = nodeWithPosition;
      const { width, height } = nodeWithPosition;

      return {
        id: node.id,
        position: {
          x: x - (width ?? nodeWidth) / 2,
          y: y - (height ?? nodeHeight) / 2,
        },
      };
    })
    .filter((item): item is LayoutResult[number] => item !== null);

  return result;
}

export function useGraphLayout(): UseGraphLayoutResult {
  const nodes = useGraphStore((state) => state.nodes);
  const edges = useGraphStore((state) => state.edges);
  const updateNode = useGraphStore((state) => state.updateNode);

  const layout = useCallback(
    (options: LayoutOptions = {}): LayoutResult => {
      const nodesInput = nodes.map((node) => ({
        id: node.id,
        width: node.width,
        height: node.height,
      }));

      const edgesInput = edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
      }));

      const result = getLayoutedElements(nodesInput, edgesInput, options);

      result.forEach(({ id, position }) => {
        updateNode(id, { position }, { isVisualOnly: true });
      });

      return result;
    },
    [edges, nodes, updateNode],
  );

  return { layout };
}
