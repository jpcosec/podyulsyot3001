import { Toaster } from '@/components/ui/sonner';

import type { ASTEdge, ASTNode } from '@/stores/types';

/** L2: Main editor container - canvas + sidebar + panels */
import { GraphCanvas } from './GraphCanvas';
import { useKeyboard } from './hooks/use-keyboard';
import { DeleteConfirm } from './components/DeleteConfirm';
import { CommandMenu } from './components/CommandMenu';
import { EdgeInspector } from './panels/EdgeInspector';
import { NodeInspector } from './panels/NodeInspector';
import { CanvasSidebar } from './sidebar/CanvasSidebar';
import { useUIStore } from '@/stores/ui-store';
import { useGraphStore } from '@/stores/graph-store';
import { toast } from 'sonner';

interface GraphEditorProps {
  initialNodes: ASTNode[];
  initialEdges: ASTEdge[];
  onSave: () => void;
}

export function GraphEditor({ initialNodes, initialEdges, onSave }: GraphEditorProps) {
  useKeyboard();

  void initialNodes;
  void initialEdges;

  const deleteConfirmOpen = useUIStore((state) => state.deleteConfirmOpen);
  const deleteTarget = useUIStore((state) => state.deleteTarget);
  const closeDeleteConfirm = useUIStore((state) => state.closeDeleteConfirm);
  const executePendingDelete = useUIStore((state) => state.executePendingDelete);
  const commandDialogOpen = useUIStore((state) => state.commandDialogOpen);
  const closeCommandDialog = useUIStore((state) => state.closeCommandDialog);
  const removeElements = useGraphStore((state) => state.removeElements);

  const handleConfirm = () => {
    executePendingDelete(removeElements);
    toast.success('Selection deleted');
  };

  return (
    <div className="flex h-screen w-full overflow-hidden px-4 pb-4 pt-4">
      <div className="relative flex-1 overflow-hidden rounded-[2rem] border border-white/8 shadow-[0_30px_90px_rgba(0,0,0,0.28)]">
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-start justify-between px-6 py-5">
          <div className="glass-panel max-w-md rounded-2xl px-4 py-3">
            <p className="font-mono text-[11px] uppercase tracking-[0.32em] text-primary">Graph Studio</p>
            <h1 className="mt-2 font-headline text-2xl font-bold text-on-surface">Command your review topology</h1>
            <p className="mt-1 text-sm text-muted-foreground">Shape nodes, wire relationships, and keep the whole system legible at a glance.</p>
          </div>

          <div className="glass-panel rounded-2xl px-4 py-3 text-right">
            <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">Workspace</p>
            <p className="mt-1 text-sm font-medium text-on-surface">Live canvas</p>
            <p className="text-xs text-muted-foreground">Save, inspect, and refactor visually</p>
          </div>
        </div>

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(0,242,255,0.08),transparent_26%),radial-gradient(circle_at_bottom_left,rgba(255,170,0,0.08),transparent_24%)]" />
        <div className="relative h-full">
          <GraphCanvas />
        </div>
      </div>
      <CanvasSidebar onSave={onSave} />
      <NodeInspector />
      <EdgeInspector />
      <DeleteConfirm
        open={deleteConfirmOpen}
        onOpenChange={(open) => !open && closeDeleteConfirm()}
        target={deleteTarget}
        onConfirm={handleConfirm}
      />
      <CommandMenu open={commandDialogOpen} onOpenChange={closeCommandDialog} onSave={onSave} />
      <Toaster />
    </div>
  );
}
