import { describe, expect, it } from 'vitest';
import { z } from 'zod';

import { NodeTypeRegistry } from './registry';

function buildRegistry() {
  const testRegistry = new NodeTypeRegistry();

  testRegistry.register({
    typeId: 'person',
    label: 'Person',
    icon: 'user',
    category: 'entity',
    colorToken: 'token-person',
    payloadSchema: z.object({
      name: z.string().min(1),
    }),
    sanitizer: (payload) => {
      const candidate = payload as Record<string, unknown>;
      return { ...candidate, name: String(candidate.name).trim() };
    },
    renderers: {
      dot: () => null,
      label: () => null,
      detail: () => null,
    },
    defaultSize: { width: 200, height: 80 },
    allowedConnections: ['skill'],
  });

  return testRegistry;
}

describe('NodeTypeRegistry (GRP-001-03)', () => {
  it('registers and retrieves definitions', () => {
    const testRegistry = buildRegistry();

    expect(testRegistry.get('person')?.label).toBe('Person');
  });

  it('validates payloads with zod schema', () => {
    const testRegistry = buildRegistry();

    const valid = testRegistry.validatePayload('person', { name: 'Ada' });
    const invalid = testRegistry.validatePayload('person', { name: '' });

    expect(valid.success).toBe(true);
    expect(invalid.success).toBe(false);
  });

  it('handles unknown type validation gracefully', () => {
    const testRegistry = buildRegistry();

    const result = testRegistry.validatePayload('missing', { name: 'Ada' });

    expect(result.success).toBe(false);
  });

  it('sanitizes payload when sanitizer exists', () => {
    const testRegistry = buildRegistry();

    const sanitized = testRegistry.sanitizePayload('person', { name: ' Ada ' }) as {
      name: string;
    };

    expect(sanitized.name).toBe('Ada');
  });

  it('checks allowed outgoing connections', () => {
    const testRegistry = buildRegistry();

    expect(testRegistry.canConnect('person', 'skill')).toBe(true);
    expect(testRegistry.canConnect('person', 'project')).toBe(false);
  });
});
