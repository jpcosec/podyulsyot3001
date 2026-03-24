import dagre from '@dagrejs/dagre';
import type { DocumentSchema, SchemaNodeType } from '../../../schemas/types';
import type { SimpleNode, SimpleEdge } from '../../../pages/global/KnowledgeGraph';

const NODE_WIDTH = 180;
const NODE_HEIGHT = 48;

function applyDagreLayout(nodes: SimpleNode[], edges: SimpleEdge[]): SimpleNode[] {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: 'LR', nodesep: 52, ranksep: 120, marginx: 24, marginy: 24 });
  nodes.forEach((n) => graph.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach((e) => graph.setEdge(e.source, e.target));
  dagre.layout(graph);
  return nodes.map((n) => {
    const pos = graph.node(n.id) as { x: number; y: number } | undefined;
    return pos ? { ...n, position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 } } : n;
  });
}

function renderToken(type: SchemaNodeType): string {
  const map: Record<string, string> = {
    root:      'root',
    abstract:  'abstract',
    entity:    'entry',
    skill:     'skill',
    edge_node: 'edge_node',
    value:     'value',
  };
  return map[type.color_token] ?? type.color_token;
}

export function schemaToGraph(schema: DocumentSchema): {
  nodes: SimpleNode[];
  edges: SimpleEdge[];
} {
  const nodes: SimpleNode[] = [];
  const edges: SimpleEdge[] = [];

  for (const type of schema.node_types) {
    if (type.render_as === 'attribute') continue;

    const colorToken = schema.visual_encoding.color_tokens[type.color_token];

    nodes.push({
      id: type.id,
      type: 'simple',
      position: { x: 0, y: 0 },
      data: {
        name: type.label,
        category: renderToken(type),
        properties: {
          render_as: type.render_as,
          ...(type.abstract ? { abstract: 'true' } : {}),
          ...(type.variant_of ? { variant_of: type.variant_of } : {}),
        },
        meta: {
          schemaType: type,
          colorToken,
        },
      },
    });

    if (type.variant_of) {
      edges.push({
        id: `extends:${type.id}`,
        source: type.id,
        target: type.variant_of,
        data: {
          relationType: 'extends',
          properties: { label: 'variant of' },
        },
      });
    }
  }

  for (const et of schema.edge_types) {
    if (et.id === 'extends') continue;
    const edgeColor = schema.visual_encoding.edge_color_tokens[et.color_token];
    edges.push({
      id: `edge:${et.id}`,
      source: et.from,
      target: et.to,
      data: {
        relationType: et.id,
        properties: {
          label: et.label,
          ...(et.cardinality ? { cardinality: et.cardinality } : {}),
        },
        meta: { edgeColor },
      },
    });
  }

  return { nodes: applyDagreLayout(nodes, edges), edges };
}
