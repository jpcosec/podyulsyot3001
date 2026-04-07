import { describe, expect, it } from 'vitest';
import { z } from 'zod';

import { schemaToGraph, schemaToGraphWithRegistry } from './schema-to-graph';
import type { RawData } from './types';
import { NodeTypeRegistry, registry } from '@/schema/registry';
import { registerDefaultNodeTypes } from '@/schema/register-defaults';

function createRegistry(): NodeTypeRegistry {
  const localRegistry = new NodeTypeRegistry();

  localRegistry.register({
    typeId: 'person',
    label: 'Person',
    icon: 'user',
    category: 'entity',
    colorToken: 'token-person',
    payloadSchema: z.object({
      name: z.string().trim().min(1),
      role: z.string().optional(),
    }),
    sanitizer: (payload) => {
      const candidate = payload as Record<string, unknown>;
      return {
        ...candidate,
        name: String(candidate.name).trim(),
      };
    },
    renderers: {
      dot: () => null,
      label: () => null,
      detail: () => null,
    },
    defaultSize: { width: 200, height: 80 },
    allowedConnections: ['skill'],
  });

  localRegistry.register({
    typeId: 'skill',
    label: 'Skill',
    icon: 'wrench',
    category: 'component',
    colorToken: 'token-skill',
    payloadSchema: z.object({
      name: z.string().trim().min(1),
      level: z.string().optional(),
    }),
    renderers: {
      dot: () => null,
      label: () => null,
      detail: () => null,
    },
    defaultSize: { width: 180, height: 60 },
    allowedConnections: ['person'],
  });

  return localRegistry;
}

describe('schemaToGraph (GRP-001-02)', () => {
  it('translates valid raw data into nodes and edges', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'person',
          name: '  Ada ',
          properties: { role: 'Engineer' },
          children: [
            {
              id: 'n-2',
              type: 'skill',
              name: 'Algorithms',
              properties: { level: 'advanced' },
            },
          ],
        },
      ],
      edges: [
        {
          id: 'e-1',
          source: 'n-1',
          target: 'n-2',
          relationType: 'has',
        },
      ],
    };

    const graph = schemaToGraphWithRegistry(rawData, createRegistry());
    const personNode = graph.nodes.find((node) => node.id === 'n-1');
    const skillNode = graph.nodes.find((node) => node.id === 'n-2');

    expect(graph.errors).toEqual([]);
    expect(graph.edges).toHaveLength(1);
    expect(personNode?.type).toBe('node');
    expect(personNode?.data.visualToken).toBe('token-person');
    const personPayload = personNode?.data.payload as { value?: Record<string, unknown> } | undefined;
    expect(personPayload?.value).toMatchObject({ name: 'Ada' });
    expect(skillNode?.parentId).toBe('n-1');
  });

  it('emits an error node when type is unknown', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'unknown-type',
          name: 'Ghost',
          properties: {},
        },
      ],
      edges: [],
    };

    const graph = schemaToGraph(rawData);

    expect(graph.nodes[0].type).toBe('error');
    expect(graph.errors).toEqual([
      {
        nodeId: 'n-1',
        message: 'Unknown node type: unknown-type',
      },
    ]);
  });

  it('keeps rawNode.name canonical during payload assembly', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'person',
          name: '  Ada Lovelace  ',
          properties: { name: 'Wrong Name', role: 'Engineer' },
        },
      ],
      edges: [],
    };

    const graph = schemaToGraphWithRegistry(rawData, createRegistry());

    expect(graph.errors).toEqual([]);
    expect(graph.nodes[0].type).toBe('node');
    const nodePayload = graph.nodes[0].data.payload as { value?: Record<string, unknown> } | undefined;
    expect(nodePayload?.value).toMatchObject({
      name: 'Ada Lovelace',
      role: 'Engineer',
    });
  });

  it('maps rawNode.name to title for title-based schemas', () => {
    const localRegistry = new NodeTypeRegistry();

    localRegistry.register({
      typeId: 'document',
      label: 'Document',
      icon: 'file',
      category: 'content',
      colorToken: 'token-document',
      payloadSchema: z.object({
        title: z.string().min(1),
        kind: z.string().optional(),
      }),
      renderers: {
        dot: () => null,
        label: () => null,
        detail: () => null,
      },
      defaultSize: { width: 200, height: 80 },
      allowedConnections: [],
    });

    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'document',
          name: 'Architecture Decision Record',
          properties: { title: 'Wrong Title', kind: 'adr' },
        },
      ],
      edges: [],
    };

    const graph = schemaToGraphWithRegistry(rawData, localRegistry);

    expect(graph.errors).toEqual([]);
    expect(graph.nodes[0].type).toBe('node');
    const nodePayload = graph.nodes[0].data.payload as { value?: Record<string, unknown> } | undefined;
    expect(nodePayload?.value).toMatchObject({
      title: 'Architecture Decision Record',
      kind: 'adr',
    });
  });

  it('uses registered defaults in schemaToGraph', () => {
    registerDefaultNodeTypes();

    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'person',
          name: 'Workbench Entity',
          properties: { category: 'document' },
        },
      ],
      edges: [],
    };

    const graph = schemaToGraph(rawData);

    expect(graph.errors).toEqual([]);
    expect(graph.nodes[0].type).toBe('node');
    expect(graph.nodes[0].data.typeId).toBe('person');
  });

  it('requires schema registration before translation', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'person',
          name: 'Bootstrap User',
          properties: { role: 'Reviewer' },
        },
      ],
      edges: [],
    };

    const graph = schemaToGraphWithRegistry(rawData, new NodeTypeRegistry());

    expect(graph.nodes[0].type).toBe('error');
    expect(graph.errors).toEqual([
      {
        nodeId: 'n-1',
        message: 'Unknown node type: person',
      },
    ]);
  });

  it('accepts section.order as a string via default schema coercion', () => {
    registerDefaultNodeTypes();

    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'section',
          name: 'Experience',
          properties: { order: '2' },
        },
      ],
      edges: [],
    };

    const graph = schemaToGraph(rawData);

    expect(graph.errors).toEqual([]);
    expect(graph.nodes[0].type).toBe('node');
    const nodePayload = graph.nodes[0].data.payload as { value?: Record<string, unknown> } | undefined;
    expect(nodePayload?.value).toMatchObject({
      title: 'Experience',
      order: 2,
    });
  });

  it('emits an error node when validation fails', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'person',
          name: '',
          properties: {},
        },
      ],
      edges: [],
    };

    const graph = schemaToGraphWithRegistry(rawData, createRegistry());

    expect(graph.nodes[0].type).toBe('error');
    expect(graph.errors).toHaveLength(1);
    expect(graph.errors[0].message).toContain('Validation failed');
  });

  it('skips edges that reference unknown node ids', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'person',
          name: 'Ada',
          properties: {},
        },
      ],
      edges: [
        {
          id: 'e-1',
          source: 'n-1',
          target: 'missing-node',
          relationType: 'uses',
        },
      ],
    };

    const graph = schemaToGraphWithRegistry(rawData, createRegistry());

    expect(graph.edges).toEqual([]);
  });

  it('fails unknown types gracefully through registry validation', () => {
    const result = registry.validatePayload('missing-type', { name: 'Ghost' });

    expect(result.success).toBe(false);
  });
});
