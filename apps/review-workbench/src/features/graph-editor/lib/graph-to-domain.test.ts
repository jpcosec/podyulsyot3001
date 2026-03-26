import { describe, expect, it } from 'vitest';

import { graphToDomain } from './graph-to-domain';
import type { ASTEdge, ASTNode } from './types';

describe('graphToDomain (GRP-001-02)', () => {
  it('builds a hierarchical node tree and flat edge list', () => {
    const nodes: ASTNode[] = [
      {
        id: 'root',
        type: 'node',
        position: { x: 0, y: 0 },
        data: {
          typeId: 'person',
          payload: { typeId: 'person', value: { name: 'Ada' } },
          properties: { role: 'Engineer' },
        },
      },
      {
        id: 'child',
        type: 'node',
        position: { x: 100, y: 100 },
        parentId: 'root',
        data: {
          typeId: 'skill',
          payload: { typeId: 'skill', value: { name: 'TypeScript' } },
          properties: { level: 'advanced' },
        },
      },
      {
        id: 'error-node',
        type: 'error',
        position: { x: 200, y: 200 },
        data: {
          typeId: 'error',
          payload: { typeId: 'error', value: { message: 'broken' } },
          properties: {},
        },
      },
    ];

    const edges: ASTEdge[] = [
      {
        id: 'e-1',
        source: 'root',
        target: 'child',
        type: 'floating',
        data: {
          relationType: 'has',
          properties: { confidence: 'high' },
        },
      },
      {
        id: 'e-2',
        source: 'error-node',
        target: 'root',
        type: 'floating',
        data: {
          relationType: 'broken-link',
          properties: {},
        },
      },
    ];

    const domain = graphToDomain(nodes, edges);

    expect(domain.nodes).toHaveLength(1);
    expect(domain.nodes[0]).toMatchObject({
      id: 'root',
      name: 'Ada',
      children: [{ id: 'child', name: 'TypeScript' }],
    });
    expect(domain.edges).toEqual([
      {
        id: 'e-1',
        source: 'root',
        target: 'child',
        relationType: 'has',
        properties: { confidence: 'high' },
      },
    ]);
  });

  it('falls back to Untitled when payload name is missing', () => {
    const nodes: ASTNode[] = [
      {
        id: 'n-1',
        type: 'node',
        position: { x: 0, y: 0 },
        data: {
          typeId: 'publication',
          payload: { typeId: 'publication', value: { year: '2025' } },
          properties: {},
        },
      },
    ];

    const domain = graphToDomain(nodes, []);

    expect(domain.nodes[0].name).toBe('Untitled');
  });

  it('ignores self-parenting nodes to avoid circular children', () => {
    const nodes: ASTNode[] = [
      {
        id: 'self',
        type: 'node',
        position: { x: 0, y: 0 },
        parentId: 'self',
        data: {
          typeId: 'category',
          payload: { typeId: 'category', value: { name: 'Self Node' } },
          properties: {},
        },
      },
    ];

    const domain = graphToDomain(nodes, []);

    expect(domain.nodes).toHaveLength(1);
    expect(domain.nodes[0]).toMatchObject({
      id: 'self',
      name: 'Self Node',
      children: [],
    });
    expect(domain.nodes[0].children).not.toContain(domain.nodes[0]);
  });

  it('treats mutually cyclic parent references as roots', () => {
    const nodes: ASTNode[] = [
      {
        id: 'a',
        type: 'node',
        position: { x: 0, y: 0 },
        parentId: 'b',
        data: {
          typeId: 'category',
          payload: { typeId: 'category', value: { name: 'Node A' } },
          properties: {},
        },
      },
      {
        id: 'b',
        type: 'node',
        position: { x: 100, y: 0 },
        parentId: 'a',
        data: {
          typeId: 'category',
          payload: { typeId: 'category', value: { name: 'Node B' } },
          properties: {},
        },
      },
    ];

    const domain = graphToDomain(nodes, []);

    expect(domain.nodes).toHaveLength(2);
    expect(domain.nodes).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: 'a', children: [] }),
        expect.objectContaining({ id: 'b', children: [] }),
      ])
    );
  });
});
