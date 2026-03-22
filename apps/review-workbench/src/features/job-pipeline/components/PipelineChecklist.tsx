import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { cn } from '../../../utils/cn';
import type { StageItem } from '../../../types/api.types';

interface Props {
  stages: StageItem[];
}

export function PipelineChecklist({ stages }: Props) {
  return (
    <div className="bg-surface-low panel-border p-6">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em] mb-4">Pipeline Checklist</p>
      <div className="space-y-3">
        {stages.map(stage => {
          const isDone = stage.status === 'approved';
          const isFailed = stage.status === 'error';

          return (
            <div key={stage.name} className="flex items-center gap-3">
              {isDone ? (
                <CheckCircle size={16} className="text-primary flex-shrink-0" />
              ) : isFailed ? (
                <XCircle size={16} className="text-error flex-shrink-0" />
              ) : (
                <Clock size={16} className="text-on-muted flex-shrink-0" />
              )}
              <span className={cn(
                'font-headline uppercase tracking-widest text-sm',
                isDone ? 'text-on-surface' : isFailed ? 'text-error' : 'text-on-muted'
              )}>
                {stage.name.replace(/_/g, ' ')}
              </span>
              <span className={cn(
                'font-mono text-[10px] ml-auto',
                isDone ? 'text-primary' : isFailed ? 'text-error' : 'text-on-muted'
              )}>
                {stage.status.toUpperCase()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
