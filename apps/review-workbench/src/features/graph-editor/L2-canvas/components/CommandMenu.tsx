import { useEffect } from 'react';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

interface CommandMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: () => void;
}

export function CommandMenu({ open, onOpenChange, onSave }: CommandMenuProps) {
  const nodes = useGraphStore((state) => state.nodes);
  const setFocusedNode = useUIStore((state) => state.setFocusedNode);
  const setEditorState = useUIStore((state) => state.setEditorState);
  const undo = useGraphStore((state) => state.undo);
  const redo = useGraphStore((state) => state.redo);

  const handleSelectNode = (nodeId: string) => {
    setFocusedNode(nodeId);
    setEditorState('focus');
    onOpenChange(false);
  };

  const handleSave = () => {
    onSave();
    onOpenChange(false);
  };

  const handleUndo = () => {
    undo();
    onOpenChange(false);
  };

  const handleRedo = () => {
    redo();
    onOpenChange(false);
  };

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [open, onOpenChange]);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Actions">
          <CommandItem onSelect={handleSave}>
            <span>Save Graph</span>
            <CommandShortcut>⌘S</CommandShortcut>
          </CommandItem>
          <CommandItem onSelect={handleUndo}>
            <span>Undo</span>
            <CommandShortcut>⌘Z</CommandShortcut>
          </CommandItem>
          <CommandItem onSelect={handleRedo}>
            <span>Redo</span>
            <CommandShortcut>⌘⇧Z</CommandShortcut>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Nodes">
          {nodes.map((node) => (
            <CommandItem
              key={node.id}
              value={node.data.visualToken || node.id}
              onSelect={() => handleSelectNode(node.id)}
            >
              <span>{node.data.visualToken || node.id}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}