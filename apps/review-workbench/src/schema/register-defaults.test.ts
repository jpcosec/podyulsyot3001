import { describe, expect, it } from 'vitest';

import { registry } from './registry';
import { registerDefaultNodeTypes } from './register-defaults';

describe('registerDefaultNodeTypes (GRP-001-03)', () => {
  it('registers the expected placeholder node types', () => {
    registerDefaultNodeTypes();

    const registeredTypes = registry.getAll().map((definition) => definition.typeId);

    expect(registeredTypes).toEqual(
      expect.arrayContaining([
        'person',
        'skill',
        'project',
        'publication',
        'concept',
        'document',
        'section',
        'entry',
      ]),
    );
  });
});
