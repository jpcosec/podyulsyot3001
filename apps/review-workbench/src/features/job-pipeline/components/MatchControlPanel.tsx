import { cn } from '../../../utils/cn';
import { Button } from '../../../components/atoms/Button';
import type { GraphNode, GraphEdge } from '../../../types/api.types';

interface Props {
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  onOpenDecisionModal: () => void;
  isSaving: boolean;
  onSave: () => void;
  onUpdateRequirement?: (id: string, field: 'priority' | 'text', value: string) => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  must: 'bg-error/20 text-error border-error/30',
  should: 'bg-secondary/20 text-secondary border-secondary/30',
  nice_to_have: 'bg-primary/20 text-primary border-primary/30',
};

function ScoreBar({ score }: { score: number }) {
  const color = score >= 0.7 ? 'bg-primary' : score >= 0.3 ? 'bg-secondary' : 'bg-error';
  return (
    <div className="mt-1">
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1 bg-surface-high">
          <div className={cn('h-full', color)} style={{ width: `${score * 100}%` }} />
        </div>
        <span className="font-mono text-[9px] text-on-muted">{Math.round(score * 100)}%</span>
      </div>
    </div>
  );
}

function RequirementDetail({ node }: { node: GraphNode }) {
  const priority = (node as GraphNode & { priority?: string }).priority ?? 'must';
  const score = (node as GraphNode & { score?: number }).score;
  const chipClass = PRIORITY_COLORS[priority] ?? PRIORITY_COLORS['must'];

  return (
    <div className="space-y-3">
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Priority</p>
        <span className={cn(
          'inline-block font-mono text-[9px] uppercase tracking-widest border px-1.5 py-0.5',
          chipClass
        )}>
          {priority.replace(/_/g, ' ')}
        </span>
      </div>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Requirement</p>
        <p className="font-body text-xs text-on-surface leading-relaxed">{node.label}</p>
      </div>
      {score != null && (
        <div>
          <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Best Match Score</p>
          <ScoreBar score={score} />
        </div>
      )}
    </div>
  );
}

function ProfileDetail({ node }: { node: GraphNode }) {
  const parts = node.label.split(':');
  const category = parts[0]?.trim() ?? 'profile';
  const summary = parts.length > 1 ? parts.slice(1).join(':').trim() : node.label;

  return (
    <div className="space-y-3">
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Evidence ID</p>
        <p className="font-mono text-[9px] text-primary">{node.id}</p>
      </div>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Category</p>
        <span className="inline-block font-mono text-[9px] uppercase tracking-widest border px-1.5 py-0.5 bg-primary/10 text-primary border-primary/30">
          {category}
        </span>
      </div>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Summary</p>
        <p className="font-body text-xs text-on-surface leading-relaxed">{summary}</p>
      </div>
    </div>
  );
}

function EdgeDetail({ edge }: { edge: GraphEdge }) {
  const score = edge.score ?? 0;
  return (
    <div className="space-y-3">
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Match Score</p>
        <ScoreBar score={score} />
      </div>
      {edge.reasoning && (
        <div>
          <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Reasoning</p>
          <p className="font-body text-xs text-on-surface leading-relaxed">{edge.reasoning}</p>
        </div>
      )}
    </div>
  );
}

export function MatchControlPanel({ selectedNode, selectedEdge, onOpenDecisionModal, isSaving, onSave }: Props) {
  return (
    <div className="w-80 bg-background border-l border-secondary/20 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em]">Phase</p>
        <p className="font-headline font-bold text-on-surface uppercase tracking-widest text-sm">Match</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {selectedNode ? (
          <div>
            <p className="font-mono text-[10px] text-on-muted uppercase mb-3">
              {selectedNode.kind === 'requirement' ? 'Requirement' : 'Profile'} Node
            </p>
            {selectedNode.kind === 'requirement'
              ? <RequirementDetail node={selectedNode} />
              : <ProfileDetail node={selectedNode} />
            }
          </div>
        ) : selectedEdge ? (
          <div>
            <p className="font-mono text-[10px] text-on-muted uppercase mb-3">Selected Edge</p>
            <EdgeDetail edge={selectedEdge} />
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
