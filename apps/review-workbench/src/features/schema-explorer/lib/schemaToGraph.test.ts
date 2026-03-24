import { describe, test, expect } from 'vitest';
import cvSchema from '../../../schemas/cv.schema.json';
import type { DocumentSchema } from '../../../schemas/types';
import { schemaToGraph } from './schemaToGraph';

const schema = cvSchema as DocumentSchema;

describe('cv.schema.json shape', () => {
  test('has required top-level keys', () => {
    expect(schema.document).toBeDefined();
    expect(schema.node_types).toBeInstanceOf(Array);
    expect(schema.edge_types).toBeInstanceOf(Array);
    expect(schema.visual_encoding).toBeDefined();
  });

  test('root_type exists in node_types', () => {
    const rootId = schema.document.root_type;
    const root = schema.node_types.find(t => t.id === rootId);
    expect(root).toBeDefined();
    expect(root?.render_as).toBe('group');
  });

  test('all variant_of references point to existing types', () => {
    const typeIds = new Set(schema.node_types.map(t => t.id));
    for (const t of schema.node_types) {
      if (t.variant_of) {
        expect(typeIds.has(t.variant_of), `${t.id}.variant_of="${t.variant_of}" not found`).toBe(true);
      }
    }
  });

  test('all edge from/to point to existing types', () => {
    const typeIds = new Set(schema.node_types.map(t => t.id));
    for (const e of schema.edge_types) {
      expect(typeIds.has(e.from), `edge ${e.id}.from="${e.from}" not found`).toBe(true);
      expect(typeIds.has(e.to), `edge ${e.id}.to="${e.to}" not found`).toBe(true);
    }
  });

  test('all color_tokens referenced in node_types exist in visual_encoding', () => {
    const tokens = new Set(Object.keys(schema.visual_encoding.color_tokens));
    for (const t of schema.node_types) {
      expect(tokens.has(t.color_token), `node ${t.id}.color_token="${t.color_token}" not in visual_encoding`).toBe(true);
    }
  });
});

describe('schemaToGraph', () => {
  const { nodes, edges } = schemaToGraph(schema);

  test('produces one node per non-attribute type', () => {
    const nonAttr = schema.node_types.filter(t => t.render_as !== 'attribute');
    expect(nodes).toHaveLength(nonAttr.length);
  });

  test('attribute types are not in nodes', () => {
    const attrIds = schema.node_types.filter(t => t.render_as === 'attribute').map(t => t.id);
    for (const id of attrIds) {
      expect(nodes.find(n => n.id === id)).toBeUndefined();
    }
  });

  test('each node has a name and category from schema', () => {
    for (const node of nodes) {
      expect(typeof node.data.name).toBe('string');
      expect(typeof node.data.category).toBe('string');
    }
  });

  test('edges are produced for each edge_type', () => {
    expect(edges.length).toBeGreaterThanOrEqual(schema.edge_types.length);
  });

  test('variant_of types get an extends edge to their parent', () => {
    const variantTypes = schema.node_types.filter(t => t.variant_of);
    for (const vt of variantTypes) {
      const extendsEdge = edges.find(
        e => e.source === vt.id && e.target === vt.variant_of
      );
      expect(extendsEdge, `no extends edge for ${vt.id}`).toBeDefined();
    }
  });

  test('color from visual_encoding is stored in node meta', () => {
    const rootNode = nodes.find(n => n.id === schema.document.root_type);
    expect(rootNode?.data.meta).toBeDefined();
  });
});
