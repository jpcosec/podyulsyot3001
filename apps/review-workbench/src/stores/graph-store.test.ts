import { beforeEach, describe, expect, it } from 'vitest';

import { useGraphStore } from './graph-store';
import type { ASTEdge, ASTNode } from './types';

const nodeA: ASTNode = {
  id: 'n-a',
  type: 'simple',
  position: { x: 10, y: 20 },
  data: {
    typeId: 'entity',
    payload: { typeId: 'entity', value: { label: 'A' } },
    properties: { label: 'A' },
  },
};

const nodeB: ASTNode = {
  id: 'n-b',
  type: 'simple',
  position: { x: 40, y: 60 },
  data: {
    typeId: 'entity',
    payload: { typeId: 'entity', value: { label: 'B' } },
    properties: { label: 'B' },
  },
};

const edgeAB: ASTEdge = {
  id: 'e-ab',
  source: 'n-a',
  target: 'n-b',
  type: 'floating',
  data: {
    relationType: 'linked',
    properties: {},
  },
};

beforeEach(() => {
  useGraphStore.setState(useGraphStore.getInitialState(), true);
});

describe('useGraphStore (GRP-001-01)', () => {
  it('tracks dirty state across markSaved and updates', () => {
    const store = useGraphStore.getState();
    store.loadGraph([nodeA], []);

    expect(useGraphStore.getState().isDirty()).toBe(false);

    useGraphStore.getState().updateNode('n-a', { position: { x: 11, y: 22 } });
    expect(useGraphStore.getState().isDirty()).toBe(true);

    useGraphStore.getState().markSaved();
    expect(useGraphStore.getState().isDirty()).toBe(false);
  });

  it('does not add visual-only updates to semantic history', () => {
    useGraphStore.getState().loadGraph([nodeA], []);
    useGraphStore.getState().updateNode('n-a', { hidden: true }, { isVisualOnly: true });

    const state = useGraphStore.getState();
    expect(state.undoStack).toHaveLength(0);
    expect(state.nodes[0]?.hidden).toBe(true);
  });

  it('supports semantic undo/redo roundtrip', () => {
    useGraphStore.getState().loadGraph([nodeA], []);
    useGraphStore.getState().addElements([nodeB], [edgeAB]);

    expect(useGraphStore.getState().nodes.map((node) => node.id)).toEqual(['n-a', 'n-b']);

    useGraphStore.getState().undo();
    expect(useGraphStore.getState().nodes.map((node) => node.id)).toEqual(['n-a']);

    useGraphStore.getState().redo();
    expect(useGraphStore.getState().nodes.map((node) => node.id)).toEqual(['n-a', 'n-b']);
    expect(useGraphStore.getState().edges.map((edge) => edge.id)).toEqual(['e-ab']);
  });

  it('removeElements removes selected nodes and connected edges', () => {
    useGraphStore.getState().loadGraph([nodeA, nodeB], [edgeAB]);
    useGraphStore.getState().removeElements(['n-a'], []);

    const state = useGraphStore.getState();
    expect(state.nodes.map((node) => node.id)).toEqual(['n-b']);
    expect(state.edges).toHaveLength(0);
    expect(state.undoStack[0]?.type).toBe('DELETE_ELEMENTS');
  });
});
