import { describe, expect, it } from 'vitest';

import { COLLAPSED_KEY, getNextCollapseProperties, isCollapsed } from './GroupShell';
import type { ASTNode } from '@/stores/types';

function makeGroupData(collapsed: string | undefined): ASTNode['data'] {
  return {
    typeId: 'group',
    payload: { typeId: 'group', value: { title: 'Team' } },
    properties: collapsed ? { [COLLAPSED_KEY]: collapsed } : {},
  };
}

describe('GroupShell helpers (GRP-001-05)', () => {
  it('reads collapsed state from node properties', () => {
    expect(isCollapsed(makeGroupData('true'))).toBe(true);
    expect(isCollapsed(makeGroupData('false'))).toBe(false);
    expect(isCollapsed(makeGroupData(undefined))).toBe(false);
  });

  it('toggles collapsed property while preserving existing keys', () => {
    const current = { [COLLAPSED_KEY]: 'false', section: 'alpha' };

    const toggled = getNextCollapseProperties(current, false);

    expect(toggled).toEqual({ [COLLAPSED_KEY]: 'true', section: 'alpha' });
  });
});
