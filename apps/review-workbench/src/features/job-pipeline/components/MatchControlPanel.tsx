import { Button } from '../../../components/atoms/Button';
import type { GraphNode, GraphEdge } from '../../../types/api.types';

interface Props {
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  onOpenDecisionModal: () => void;
  isSaving: boolean;
  onSave: () => void;
}

export function MatchControlPanel({ selectedNode, selectedEdge, onOpenDecisionModal, isSaving, onSave }: Props) {
  const selected = selectedNode ?? selectedEdge;

  return (
    <div className="w-80 bg-background border-l border-secondary/20 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em]">Phase</p>
        <p className="font-headline font-bold text-on-surface uppercase tracking-widest text-sm">Match</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {selected ? (
          <div>
            <p className="font-mono text-[10px] text-on-muted uppercase mb-2">
              {selectedNode ? 'Selected Node' : 'Selected Edge'}
            </p>
            <pre className="bg-surface-container border border-outline/20 p-2 font-mono text-[9px] text-on-surface overflow-auto whitespace-pre-wrap text-xs">
              {JSON.stringify(selected, null, 2)}
            </pre>
          </div>
        ) : (
          <p className="font-mono text-[10px] text-on-muted uppercase">Click a node or edge</p>
        )}
      </div>

      <div className="p-4 border-t border-outline/20 space-y-2">
        <Button variant="ghost" size="sm" className="w-full justify-center" onClick={onSave} loading={isSaving}>
          SAVE (Ctrl+S)
        </Button>
        <Button variant="primary" size="sm" className="w-full justify-center" onClick={onOpenDecisionModal}>
          COMMIT MATCH (Ctrl+Enter)
        </Button>
      </div>
    </div>
  );
}
