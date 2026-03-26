import { Toaster } from '@/components/ui/sonner';

import type { ASTEdge, ASTNode } from '@/stores/types';

import { GraphCanvas } from './GraphCanvas';
import { useKeyboard } from './hooks/use-keyboard';
import { EdgeInspector } from './panels/EdgeInspector';
import { NodeInspector } from './panels/NodeInspector';
import { CanvasSidebar } from './sidebar/CanvasSidebar';

interface GraphEditorProps {
  initialNodes: ASTNode[];
  initialEdges: ASTEdge[];
  onSave: () => void;
}

export function GraphEditor({ initialNodes, initialEdges, onSave }: GraphEditorProps) {
  useKeyboard();

  void initialNodes;
  void initialEdges;

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <div className="relative flex-1">
        <GraphCanvas />
      </div>
      <CanvasSidebar onSave={onSave} />
      <NodeInspector />
      <EdgeInspector />
      <Toaster />
    </div>
  );
}
