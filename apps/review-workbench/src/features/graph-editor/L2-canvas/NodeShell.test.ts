import { describe, expect, it } from 'vitest';

import { getNodeTitle, getRenderTier, getUnknownMessage } from './NodeShell';
import type { ASTNode } from '@/stores/types';

function makeNodeData(payloadValue: unknown): ASTNode['data'] {
  return {
    typeId: 'person',
    payload: { typeId: 'person', value: payloadValue },
    properties: {},
  };
}

describe('NodeShell helpers (GRP-001-05)', () => {
  it('selects render tier from zoom thresholds', () => {
    expect(getRenderTier(0.2)).toBe('dot');
    expect(getRenderTier(0.4)).toBe('label');
    expect(getRenderTier(0.95)).toBe('detail');
  });

  it('extracts node title from name and title payload fields', () => {
    expect(getNodeTitle(makeNodeData({ name: 'Ada' }))).toBe('Ada');
    expect(getNodeTitle(makeNodeData({ title: 'System Design' }))).toBe('System Design');
    expect(getNodeTitle(makeNodeData({}))).toBe('Untitled');
  });

  it('returns unknown message only when non-empty', () => {
    expect(getUnknownMessage(makeNodeData({ message: 'Unknown node type' }))).toBe('Unknown node type');
    expect(getUnknownMessage(makeNodeData({ message: '   ' }))).toBeNull();
  });
});
