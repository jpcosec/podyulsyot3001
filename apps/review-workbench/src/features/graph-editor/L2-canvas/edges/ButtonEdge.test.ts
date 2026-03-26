import { describe, expect, it, vi } from 'vitest';

import { deleteEdge, shouldShowDeleteButton } from './ButtonEdge';

describe('ButtonEdge helpers (GRP-001-06)', () => {
  it('shows delete button when edge hit target is hovered', () => {
    expect(shouldShowDeleteButton(false, false, false)).toBe(false);
    expect(shouldShowDeleteButton(false, false, true)).toBe(true);
  });

  it('removes edge from graph store when no custom handler exists', () => {
    const removeElements = vi.fn();

    deleteEdge({ edgeId: 'edge-1', onDelete: null, removeElements });

    expect(removeElements).toHaveBeenCalledTimes(1);
    expect(removeElements).toHaveBeenCalledWith([], ['edge-1']);
  });

  it('prefers custom delete handler when provided', () => {
    const onDelete = vi.fn();
    const removeElements = vi.fn();

    deleteEdge({ edgeId: 'edge-2', onDelete, removeElements });

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith('edge-2');
    expect(removeElements).not.toHaveBeenCalled();
  });
});
