import { describe, expect, it } from 'vitest';

import { graphDataProvider } from './data-provider';

describe('graphDataProvider (Step00)', () => {
  it('returns a minimal schema contract', async () => {
    const schema = await graphDataProvider.getSchema();

    expect(schema.node_types.length).toBeGreaterThan(0);
    expect(schema.node_types[0]).toMatchObject({
      id: 'entity',
      display_name: 'Entity',
    });
  });

  it('returns a minimal graph payload contract', async () => {
    const graph = await graphDataProvider.getGraph();

    expect(graph).toMatchObject({
      nodes: expect.any(Array),
      edges: expect.any(Array),
    });
  });

  it('acknowledges save with ok response', async () => {
    await expect(graphDataProvider.saveGraph({ nodes: [], edges: [] })).resolves.toEqual({
      ok: true,
    });
  });
});
