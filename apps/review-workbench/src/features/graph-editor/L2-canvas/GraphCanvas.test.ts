import { describe, expect, it } from 'vitest';

import { buildDisplayNodes, shouldHideForTextFilter } from './GraphCanvas';
import type { ASTNode } from '@/stores/types';

function makeNode(id: string, name: string, hidden = false): ASTNode {
  return {
    id,
    type: 'node',
    position: { x: 0, y: 0 },
    hidden,
    data: {
      typeId: 'person',
      payload: {
        typeId: 'person',
        value: { name },
      },
      properties: {},
    },
  };
}

describe('GraphCanvas display filters (GRP-001-05)', () => {
  it('preserves store-level hidden flag when applying text filter', () => {
    const nodes = [makeNode('n-1', 'Ada', true), makeNode('n-2', 'Grace', false)];

    const displayNodes = buildDisplayNodes(nodes, 'Ada');

    expect(displayNodes.find((node) => node.id === 'n-1')?.hidden).toBe(true);
    expect(displayNodes.find((node) => node.id === 'n-2')?.hidden).toBe(true);
  });

  it('keeps nodes visible when text filter is empty', () => {
    const nodes = [makeNode('n-1', 'Ada')];

    const displayNodes = buildDisplayNodes(nodes, '');

    expect(displayNodes[0]?.hidden).toBe(false);
  });

  it('matches node title from payload title/name fields', () => {
    const titledNode: ASTNode = {
      ...makeNode('n-1', ''),
      data: {
        typeId: 'document',
        payload: {
          typeId: 'document',
          value: { title: 'Design Notes' },
        },
        properties: {},
      },
    };

    expect(shouldHideForTextFilter(titledNode, 'design')).toBe(false);
    expect(shouldHideForTextFilter(titledNode, 'missing')).toBe(true);
  });
});
