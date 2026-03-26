import { describe, expect, it, vi } from 'vitest';

import { applyLayoutWorkerResponse } from './use-graph-layout';

describe('useGraphLayout request correlation (GRP-001-09)', () => {
  it('ignores worker responses for different requests', () => {
    const updateNode = vi.fn();

    const result = applyLayoutWorkerResponse(
      {
        type: 'result',
        requestId: 'layout-2',
        payload: [{ id: 'node-1', position: { x: 10, y: 20 } }],
      },
      'layout-1',
      updateNode,
    );

    expect(result).toBeNull();
    expect(updateNode).not.toHaveBeenCalled();
  });

  it('applies updates only for the matching request result', () => {
    const updateNode = vi.fn();

    const result = applyLayoutWorkerResponse(
      {
        type: 'result',
        requestId: 'layout-1',
        payload: [{ id: 'node-1', position: { x: 30, y: 40 } }],
      },
      'layout-1',
      updateNode,
    );

    expect(result).toEqual([{ id: 'node-1', position: { x: 30, y: 40 } }]);
    expect(updateNode).toHaveBeenCalledTimes(1);
    expect(updateNode).toHaveBeenCalledWith(
      'node-1',
      { position: { x: 30, y: 40 } },
      { isVisualOnly: true },
    );
  });

  it('returns an empty result for matching request errors', () => {
    const updateNode = vi.fn();

    const result = applyLayoutWorkerResponse(
      {
        type: 'error',
        requestId: 'layout-1',
        error: 'Layout computation failed',
      },
      'layout-1',
      updateNode,
    );

    expect(result).toEqual([]);
    expect(updateNode).not.toHaveBeenCalled();
  });
});
