import { cn } from '../../../utils/cn';
import { StageRow } from './StageRow';
import type { StageItem } from '../../../types/api.types';

interface Props {
  source: string;
  jobId: string;
  stages: StageItem[];
}

export function PipelineTimeline({ source, jobId, stages }: Props) {
  return (
    <div className="bg-surface-low border border-outline/20 p-4">
      <div className="space-y-0">
        {stages.map((stage, idx) => (
          <div key={stage.name}>
            <div className={cn('py-3', idx < stages.length - 1 && 'border-l-2 border-outline/20 ml-[5px] pl-4')}>
              <StageRow source={source} jobId={jobId} stage={stage} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
