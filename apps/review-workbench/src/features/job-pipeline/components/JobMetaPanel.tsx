import type { JobTimeline } from '../../../types/api.types';

interface Props {
  timeline: JobTimeline;
}

export function JobMetaPanel({ timeline }: Props) {
  return (
    <div className="bg-surface-low border border-outline/20 p-4 mt-4">
      <div className="space-y-3">
        <div>
          <div className="font-mono text-[10px] text-on-muted uppercase">Thread ID</div>
          <div className="font-mono text-xs text-on-surface mt-1">{timeline.thread_id}</div>
        </div>
        <div>
          <div className="font-mono text-[10px] text-on-muted uppercase">Status</div>
          <div className="font-mono text-xs text-on-surface mt-1">{timeline.status}</div>
        </div>
        <div>
          <div className="font-mono text-[10px] text-on-muted uppercase">Updated At</div>
          <div className="font-mono text-xs text-on-surface mt-1">
            {new Date(timeline.updated_at).toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
