import { describe, expect, it } from 'vitest';

import { isEditableTarget, resolveKeyboardCommand } from './use-keyboard';

function keyEvent(key: string, flags?: Partial<Pick<KeyboardEvent, 'ctrlKey' | 'metaKey' | 'shiftKey'>>) {
  return {
    key,
    ctrlKey: flags?.ctrlKey ?? false,
    metaKey: flags?.metaKey ?? false,
    shiftKey: flags?.shiftKey ?? false,
  };
}

describe('useKeyboard key gating (GRP-001-09)', () => {
  it('enters node edit mode only when focused in browse mode', () => {
    const command = resolveKeyboardCommand(keyEvent('Enter'), {
      editorState: 'browse',
      focusedNodeId: 'node-1',
    });

    expect(command).toBe('edit-node');
    expect(
      resolveKeyboardCommand(keyEvent('Enter'), { editorState: 'browse', focusedNodeId: null }),
    ).toBeNull();
    expect(
      resolveKeyboardCommand(keyEvent('Enter'), { editorState: 'edit_node', focusedNodeId: 'node-1' }),
    ).toBeNull();
  });

  it('limits undo/redo shortcuts to browse mode with modifiers', () => {
    expect(
      resolveKeyboardCommand(keyEvent('z', { ctrlKey: true }), {
        editorState: 'browse',
        focusedNodeId: null,
      }),
    ).toBe('undo');

    expect(
      resolveKeyboardCommand(keyEvent('z', { ctrlKey: true, shiftKey: true }), {
        editorState: 'browse',
        focusedNodeId: null,
      }),
    ).toBe('redo');

    expect(
      resolveKeyboardCommand(keyEvent('Z', { ctrlKey: true, shiftKey: true }), {
        editorState: 'browse',
        focusedNodeId: null,
      }),
    ).toBe('redo');

    expect(
      resolveKeyboardCommand(keyEvent('Y', { ctrlKey: true }), {
        editorState: 'browse',
        focusedNodeId: null,
      }),
    ).toBe('redo');

    expect(
      resolveKeyboardCommand(keyEvent('z', { ctrlKey: true }), {
        editorState: 'edit_relation',
        focusedNodeId: null,
      }),
    ).toBeNull();
  });

  it('keeps delete unhandled and allows escape to exit edit modes', () => {
    expect(
      resolveKeyboardCommand(keyEvent('Delete'), {
        editorState: 'browse',
        focusedNodeId: 'node-1',
      }),
    ).toBeNull();

    expect(
      resolveKeyboardCommand(keyEvent('Escape'), {
        editorState: 'edit_relation',
        focusedNodeId: null,
      }),
    ).toBe('exit-edit-mode');
  });

  it('detects editable DOM targets for shortcut guard', () => {
    const input = { tagName: 'INPUT' } as unknown as EventTarget;
    const textarea = { tagName: 'textarea' } as unknown as EventTarget;
    const select = { tagName: 'Select' } as unknown as EventTarget;
    const contentEditable = { tagName: 'div', isContentEditable: true } as unknown as EventTarget;
    const plainDiv = { tagName: 'div' } as unknown as EventTarget;

    expect(isEditableTarget(input)).toBe(true);
    expect(isEditableTarget(textarea)).toBe(true);
    expect(isEditableTarget(select)).toBe(true);
    expect(isEditableTarget(contentEditable)).toBe(true);
    expect(isEditableTarget(plainDiv)).toBe(false);
    expect(isEditableTarget(null)).toBe(false);
  });
});
