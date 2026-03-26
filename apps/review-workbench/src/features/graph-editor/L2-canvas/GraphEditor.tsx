import { Toaster } from '@/components/ui/sonner';

import type { ASTEdge, ASTNode } from '@/stores/types';

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
    <div className="flex h-screen w-full overflow-hidden">
      <div className="relative flex-1">
        <GraphCanvas />
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
