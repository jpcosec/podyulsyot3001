import { Handle, Position } from '@xyflow/react';
import { cn } from '../../../utils/cn';

interface RequirementNodeData {
  label: string;
  score?: number;
  priority?: string;
}

interface Props {
  data: RequirementNodeData;
  selected?: boolean;
}

export function RequirementNode({ data, selected }: Props) {
  const score = data.score ?? 0;
  const borderColor = score >= 0.7
    ? 'border-l-primary'
    : score >= 0.3
    ? 'border-l-secondary'
    : 'border-l-error';

  return (
    <div className={cn(
      'bg-surface-container border border-outline/30 border-l-4 px-3 py-2 min-w-[200px] max-w-[240px]',
      borderColor,
      selected && 'border-primary/60 shadow-[0_0_8px_rgba(0,242,255,0.3)]'
    )}>
      <Handle type="target" position={Position.Left} className="!bg-primary !border-primary/50 !w-2 !h-2" />
      <p className="font-mono text-[9px] text-on-muted uppercase mb-1">{data.priority ?? 'must'}</p>
      <p className="font-body text-xs text-on-surface leading-tight">{data.label}</p>
      {score > 0 && (
        <div className="mt-2">
          <div className="h-0.5 bg-surface-high w-full">
            <div
              className={cn('h-full', score >= 0.7 ? 'bg-primary' : score >= 0.3 ? 'bg-secondary' : 'bg-error')}
              style={{ width: `${score * 100}%` }}
            />
          </div>
        </div>
      )}
      <Handle type="source" position={Position.Right} className="!bg-primary !border-primary/50 !w-2 !h-2" />
    </div>
  );
}
