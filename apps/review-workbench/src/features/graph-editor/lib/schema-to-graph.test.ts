import { describe, expect, it } from 'vitest';

import { schemaToGraph, schemaToGraphWithRegistry } from './schema-to-graph';
import type {
  RawData,
  SchemaNodeDefinition,
  SchemaRegistry,
  SchemaValidationResult,
} from './types';

function buildValidationResult(payload: unknown): SchemaValidationResult {
  if (!payload || typeof payload !== 'object') {
    return {
      success: false,
      error: { message: 'Payload must be an object' },
    };
  }

  const candidate = payload as Record<string, unknown>;
  if (typeof candidate.name !== 'string' || candidate.name.trim().length === 0) {
    return {
      success: false,
      error: { message: 'Name is required' },
    };
  }

  return {
    success: true,
    data: candidate,
  };
}

function createRegistry(definitions: SchemaNodeDefinition[]): SchemaRegistry {
  const map = new Map(definitions.map((definition) => [definition.typeId, definition]));

  return {
    get(typeId: string) {
      return map.get(typeId);
    },
  };
}

describe('schemaToGraph (GRP-001-02)', () => {
  const personDefinition: SchemaNodeDefinition = {
    typeId: 'person',
    colorToken: 'token-person',
    validate: buildValidationResult,
    sanitize: (payload) => {
      const candidate = payload as Record<string, unknown>;
      return {
        ...candidate,
        name: String(candidate.name).trim(),
      };
    },
  };

  const skillDefinition: SchemaNodeDefinition = {
    typeId: 'skill',
    colorToken: 'token-skill',
    validate: buildValidationResult,
  };

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

    const graph = schemaToGraphWithRegistry(rawData, createRegistry([personDefinition, skillDefinition]));
    const personNode = graph.nodes.find((node) => node.id === 'n-1');
    const skillNode = graph.nodes.find((node) => node.id === 'n-2');

    expect(graph.errors).toEqual([]);
    expect(graph.edges).toHaveLength(1);
    expect(personNode?.type).toBe('node');
    expect(personNode?.data.visualToken).toBe('token-person');
    expect(personNode?.data.payload.value).toMatchObject({ name: 'Ada' });
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

    const graph = schemaToGraphWithRegistry(rawData, createRegistry([personDefinition]));

    expect(graph.errors).toEqual([]);
    expect(graph.nodes[0].type).toBe('node');
    expect(graph.nodes[0].data.payload.value).toMatchObject({
      name: 'Ada Lovelace',
      role: 'Engineer',
    });
  });

  it('uses runtime registry defaults in schemaToGraph', () => {
    const rawData: RawData = {
      nodes: [
        {
          id: 'n-1',
          type: 'entity',
          name: 'Workbench Entity',
          properties: { category: 'document' },
        },
      ],
      edges: [],
    };

    const graph = schemaToGraph(rawData);

    expect(graph.errors).toEqual([]);
    expect(graph.nodes[0].type).toBe('node');
    expect(graph.nodes[0].data.typeId).toBe('entity');
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

    const graph = schemaToGraphWithRegistry(rawData, createRegistry([personDefinition]));

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

    const graph = schemaToGraphWithRegistry(rawData, createRegistry([personDefinition]));

    expect(graph.edges).toEqual([]);
  });
});
