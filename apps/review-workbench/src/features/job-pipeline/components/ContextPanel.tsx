import type { GraphNode, GraphEdge } from '../../../types/api.types';
import { Button } from '../../../components/atoms/Button';

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onRequestRegen: () => void;
  onApproveAll: () => void;
  isLoading: boolean;
}

export function ContextPanel({ nodes, edges, onRequestRegen, onApproveAll, isLoading }: Props) {
  const profileNodes = nodes.filter(n => n.kind === 'profile');
  const evidenceCount = edges.length;

  return (
    <div className="w-80 bg-background border-l border-secondary/20 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em]">Phase</p>
        <p className="font-headline font-bold text-secondary uppercase tracking-widest text-sm">Sculpting</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase mb-2">
            Evidence Used ({evidenceCount} links)
          </p>
          <div className="space-y-1">
            {profileNodes.slice(0, 8).map(node => (
              <div key={node.id} className="flex items-start gap-2">
                <span className="font-mono text-[9px] text-primary/60 mt-0.5 flex-shrink-0">{node.id}</span>
                <span className="font-body text-xs text-on-surface leading-tight">{node.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-outline/20 space-y-2">
        <div className="font-mono text-[9px] text-on-muted space-y-1">
          <p>Ctrl+S — Save document</p>
          <p>Ctrl+Enter — Approve current</p>
        </div>
        <Button variant="ghost" size="sm" className="w-full justify-center" onClick={onRequestRegen}>
          REQUEST REGEN
        </Button>
        <Button variant="primary" size="sm" className="w-full justify-center" onClick={onApproveAll} loading={isLoading}>
          APPROVE ALL
        </Button>
      </div>
    </div>
  );
}
