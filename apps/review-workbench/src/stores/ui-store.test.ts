import { beforeEach, describe, expect, it } from 'vitest';

import { useUIStore } from './ui-store';

beforeEach(() => {
  useUIStore.setState(useUIStore.getInitialState(), true);
});

describe('useUIStore (GRP-001-01)', () => {
  it('merges filter updates without dropping other fields', () => {
    useUIStore.getState().setFilter({ filterText: 'motor', hideNonNeighbors: false });

    const filters = useUIStore.getState().filters;
    expect(filters.filterText).toBe('motor');
    expect(filters.hideNonNeighbors).toBe(false);
    expect(filters.hiddenRelationTypes).toEqual([]);
    expect(filters.attributeFilter).toBe(null);
  });

  it('toggles sidebar open state', () => {
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(false);

    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });
});
