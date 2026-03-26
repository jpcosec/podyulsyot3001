import { describe, expect, it, vi } from 'vitest';

import { getGraphEditorPageViewState, registerSchemaTypes } from './GraphEditorPage';

describe('GraphEditorPage (GRP-001-10 blockers)', () => {
  it('prioritizes error state over loading/registration gating', () => {
    const state = getGraphEditorPageViewState({
      schemaLoading: true,
      dataLoading: true,
      isSchemaRegistered: false,
      schemaError: new Error('schema failed'),
      dataError: null,
    });

    expect(state).toBe('error');
  });

  it('maps allowed_connections into registry allowedConnections', () => {
    const register = vi.fn();

    registerSchemaTypes(
      {
        node_types: [
          {
            id: 'person',
            display_name: 'Person',
            visual: { color_token: 'token-person', icon: 'user' },
            attributes: { name: { type: 'string', required: true } },
            allowed_connections: ['skill', 'project'],
          },
          {
            id: 'skill',
            display_name: 'Skill',
            visual: { color_token: 'token-skill', icon: 'sparkles' },
            attributes: { name: { type: 'string', required: true } },
          },
        ],
      },
      { register },
    );

    expect(register).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        typeId: 'person',
        allowedConnections: ['skill', 'project'],
      }),
    );
    expect(register).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        typeId: 'skill',
        allowedConnections: [],
      }),
    );
  });
});
