import type { MatchViewData, GraphNode as ApiGraphNode } from '../../../types/api.types';
import type { SimpleNode, SimpleEdge } from '../../../pages/global/KnowledgeGraph';

export interface MatchEdits {
  addedEdges:   Array<{ source: string; target: string }>;
  removedEdges: Array<{ id: string }>;
  addedNodes:   Array<{ id: string; label: string; kind: 'profile'; category: string }>;
}

const LEFT_X = 0;
const RIGHT_X = 700;
const GROUP_WIDTH = 380;
const GROUP_HEADER = 36;
const ITEM_HEIGHT = 52;
const ITEM_PADDING = 8;
const GROUP_GAP = 16;

function groupByCategory(nodes: ApiGraphNode[]): Map<string, ApiGraphNode[]> {
  const map = new Map<string, ApiGraphNode[]>();
  for (const node of nodes) {
    const cat = node.category ?? 'general';
    const arr = map.get(cat) ?? [];
    arr.push(node);
    map.set(cat, arr);
  }
  return map;
}

function buildColumn(
  nodes: ApiGraphNode[],
  x: number,
  side: 'requirement' | 'profile',
  simpleCategory: 'entry' | 'skill',
  resultNodes: SimpleNode[],
) {
  const byCategory = groupByCategory(nodes);
  let colY = 0;

  for (const [cat, items] of byCategory) {
    const groupId = `${side}-group:${cat}`;
    const groupHeight = GROUP_HEADER + items.length * ITEM_HEIGHT + ITEM_PADDING;

    resultNodes.push({
      id: groupId,
      type: 'group',
      position: { x, y: colY },
      style: { width: GROUP_WIDTH, height: groupHeight },
      data: { name: cat, category: 'section', properties: { side } },
    });

    for (let i = 0; i < items.length; i++) {
      const item = items[i]!;
      resultNodes.push({
        id: item.id,
        type: 'simple',
        parentId: groupId,
        extent: 'parent',
        position: { x: ITEM_PADDING, y: GROUP_HEADER + i * ITEM_HEIGHT },
        data: {
          name: item.label,
          category: simpleCategory,
          properties: {
            priority: item.priority ?? '',
            score: String(item.score ?? ''),
            kind: side,
          },
          meta: { originalId: item.id, kind: side, category: cat },
        },
      });
    }

    colY += groupHeight + GROUP_GAP;
  }
}

export function matchPayloadToGraph(data: MatchViewData): { nodes: SimpleNode[]; edges: SimpleEdge[] } {
  const nodes: SimpleNode[] = [];
  const edges: SimpleEdge[] = [];

  const reqNodes = data.nodes.filter(n => n.kind === 'requirement');
  const profNodes = data.nodes.filter(n => n.kind === 'profile');

  buildColumn(reqNodes, LEFT_X,  'requirement', 'entry', nodes);
  buildColumn(profNodes, RIGHT_X, 'profile',     'skill', nodes);

  for (const edge of data.edges) {
    edges.push({
      id: `match:${edge.source}->${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'subflow',
      label: edge.score != null ? `${Math.round(edge.score * 100)}%` : undefined,
      data: {
        relationType: 'matched_by',
        properties: {
          score: String(edge.score ?? ''),
          reasoning: edge.reasoning ?? '',
        },
      },
    });
  }

  return { nodes, edges };
}

export function graphToMatchEdits(
  original: MatchViewData,
  nodes: SimpleNode[],
  edges: SimpleEdge[],
): MatchEdits {
  const originalEdgeKeys = new Set(original.edges.map(e => `${e.source}->${e.target}`));
  const currentEdgeKeys = new Set(
    edges
      .filter(e => e.data?.relationType === 'matched_by')
      .map(e => `${e.source}->${e.target}`),
  );
  const originalNodeIds = new Set(original.nodes.map(n => n.id));

  const addedEdges = edges
    .filter(e => e.data?.relationType === 'matched_by' && !originalEdgeKeys.has(`${e.source}->${e.target}`))
    .map(e => ({ source: e.source, target: e.target }));

  const removedEdges = original.edges
    .filter(e => !currentEdgeKeys.has(`${e.source}->${e.target}`))
    .map(e => ({ id: `match:${e.source}->${e.target}` }));

  const addedNodes = nodes
    .filter(n => n.data.properties['kind'] === 'profile' && !originalNodeIds.has(n.id))
    .map(n => ({
      id: n.id,
      label: n.data.name,
      kind: 'profile' as const,
      category: (n.data.meta as { category: string } | undefined)?.category ?? 'general',
    }));

  return { addedEdges, removedEdges, addedNodes };
}
