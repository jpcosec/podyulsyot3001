import { Handle, Position } from '@xyflow/react';
import { cn } from '../../../utils/cn';

interface ProfileNodeData {
  label: string;
  category?: string;
  dimmed?: boolean;
  highlighted?: boolean;
}

interface Props {
  data: ProfileNodeData;
  selected?: boolean;
  dimmed?: boolean;
  highlighted?: boolean;
}

export function ProfileNode({ data, selected }: Props) {
  const dimmed = data.dimmed;
  const highlighted = data.highlighted;

  return (
    <div className={cn(
      'bg-surface-container border border-outline/30 px-3 py-2 min-w-[160px] max-w-[200px]',
      selected && 'border-primary/60 shadow-[0_0_8px_rgba(0,242,255,0.3)]',
      highlighted && 'ring-1 ring-primary/60',
      dimmed && 'opacity-30'
    )}>
      <Handle type="target" position={Position.Left} className="!bg-primary !border-primary/50 !w-2 !h-2" />
      <p className="font-mono text-[9px] text-primary/60 uppercase mb-1">
        {data.label.split(':')[0] ?? 'profile'}
      </p>
      <p className="font-body text-xs text-on-surface leading-tight">
        {data.label.includes(':') ? data.label.split(':').slice(1).join(':').trim() : data.label}
      </p>
      <Handle type="source" position={Position.Right} className="!bg-primary !border-primary/50 !w-2 !h-2" />
    </div>
  );
}
