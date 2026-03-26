import { describe, expect, it, vi } from 'vitest';

import { collapseGroupEdges, expandGroupEdges } from './use-edge-inheritance';
import type { ASTEdge, ASTNode } from '@/stores/types';

const groupNode: ASTNode = {
  id: 'group-1',
  type: 'group',
  position: { x: 0, y: 0 },
  data: {
    typeId: 'group',
    payload: { typeId: 'group', value: {} },
    properties: {},
  },
};

const childA: ASTNode = {
  id: 'child-a',
  type: 'entity',
  parentId: 'group-1',
  position: { x: 10, y: 10 },
  data: {
    typeId: 'entity',
    payload: { typeId: 'entity', value: {} },
    properties: {},
  },
};

const externalNode: ASTNode = {
  id: 'outside',
  type: 'entity',
  position: { x: 80, y: 10 },
  data: {
    typeId: 'entity',
    payload: { typeId: 'entity', value: {} },
    properties: {},
  },
};

describe('useEdgeInheritance helpers (GRP-001-09)', () => {
  it('collapse marks inherited proxy edges', () => {
    const updateNode = vi.fn();
    const updateEdge = vi.fn();

    const edges: ASTEdge[] = [
      {
        id: 'edge-1',
        source: 'child-a',
        target: 'outside',
        type: 'floating',
        data: { relationType: 'uses', properties: { scope: 'x' } },
      },
      {
        id: 'edge-2',
        source: 'child-a',
        target: 'child-a',
        type: 'floating',
        data: { relationType: 'uses', properties: {} },
      },
    ];

    collapseGroupEdges('group-1', {
      nodes: [groupNode, childA, externalNode],
      edges,
      updateNode,
      updateEdge,
    });

    expect(updateEdge).toHaveBeenCalledTimes(1);
    expect(updateEdge).toHaveBeenCalledWith(
      'edge-1',
      expect.objectContaining({
        source: 'group-1',
        target: 'outside',
        data: expect.objectContaining({
          relationType: 'inherited',
          _originalSource: 'child-a',
          _originalTarget: 'outside',
          _originalRelationType: 'uses',
        }),
      }),
      { isVisualOnly: true },
    );
  });

  it('expand restores edge endpoints and clears inheritance metadata', () => {
    const updateNode = vi.fn();
    const updateEdge = vi.fn();

    const collapsedEdge: ASTEdge = {
      id: 'edge-1',
      source: 'group-1',
      target: 'outside',
      type: 'floating',
      data: {
        relationType: 'inherited',
        properties: { scope: 'x' },
        _originalSource: 'child-a',
        _originalTarget: 'outside',
        _originalRelationType: 'uses',
      },
      hidden: true,
    };

    expandGroupEdges('group-1', {
      nodes: [groupNode, childA, externalNode],
      edges: [collapsedEdge],
      updateNode,
      updateEdge,
    });

    expect(updateEdge).toHaveBeenCalledTimes(1);
    expect(updateEdge).toHaveBeenCalledWith(
      'edge-1',
      {
        source: 'child-a',
        target: 'outside',
        hidden: true,
        data: {
          relationType: 'uses',
          properties: { scope: 'x' },
          _originalSource: undefined,
          _originalTarget: undefined,
          _originalRelationType: undefined,
        },
      },
      { isVisualOnly: true },
    );
  });
});
