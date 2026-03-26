import { useEffect } from 'react';

import { useGraphStore } from '@/stores/graph-store';
import type { EditorState } from '@/stores/ui-store';
import { useUIStore } from '@/stores/ui-store';

type KeyboardEventLike = Pick<KeyboardEvent, 'key' | 'ctrlKey' | 'metaKey' | 'shiftKey'>;

export type KeyboardCommand = 'edit-node' | 'exit-edit-mode' | 'undo' | 'redo' | null;

interface KeyboardContext {
  editorState: EditorState;
  focusedNodeId: string | null;
}

export function isEditableTarget(target: EventTarget | null): boolean {
  if (!target || typeof target !== 'object') {
    return false;
  }

  const elementLike = target as { isContentEditable?: unknown; tagName?: unknown };

  if (elementLike.isContentEditable === true) {
    return true;
  }

  if (typeof elementLike.tagName !== 'string') {
    return false;
  }

  const tagName = elementLike.tagName.toLowerCase();
  return tagName === 'input' || tagName === 'textarea' || tagName === 'select';
}

export function resolveKeyboardCommand(
  event: KeyboardEventLike,
  context: KeyboardContext,
): KeyboardCommand {
  const { editorState, focusedNodeId } = context;
  const isMod = event.ctrlKey || event.metaKey;
  const key = event.key.toLowerCase();

  if (key === 'enter' && editorState === 'browse' && focusedNodeId) {
    return 'edit-node';
  }

  if (key === 'escape' && (editorState === 'edit_node' || editorState === 'edit_relation')) {
    return 'exit-edit-mode';
  }

  if (editorState !== 'browse' || !isMod) {
    return null;
  }

  if (key === 'z' && !event.shiftKey) {
    return 'undo';
  }

  if (key === 'y' || (key === 'z' && event.shiftKey)) {
    return 'redo';
  }

  return null;
}

export function useKeyboard() {
  const editorState = useUIStore((state) => state.editorState);
  const focusedNodeId = useUIStore((state) => state.focusedNodeId);
  const setEditorState = useUIStore((state) => state.setEditorState);
  const setFocusedNode = useUIStore((state) => state.setFocusedNode);
  const setFocusedEdge = useUIStore((state) => state.setFocusedEdge);

  const undo = useGraphStore((state) => state.undo);
  const redo = useGraphStore((state) => state.redo);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (isEditableTarget(event.target)) {
        return;
      }

      const command = resolveKeyboardCommand(event, { editorState, focusedNodeId });

      if (!command) {
        return;
      }

      event.preventDefault();

      if (command === 'edit-node') {
        setEditorState('edit_node');
        return;
      }

      if (command === 'exit-edit-mode') {
        setFocusedNode(null);
        setFocusedEdge(null);
        setEditorState('browse');
        return;
      }

      if (command === 'undo') {
        undo();
        return;
      }

      if (command === 'redo') {
        redo();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [editorState, focusedNodeId, redo, setEditorState, setFocusedEdge, setFocusedNode, undo]);
}
