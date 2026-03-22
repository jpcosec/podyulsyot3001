import type { JobTimeline } from '../../../types/api.types';

interface Props {
  timeline: JobTimeline;
}

export function MissionSummaryCard({ timeline }: Props) {
  return (
    <div className="bg-surface-low panel-border tactical-glow p-6">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em] mb-4">Mission Summary</p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase">Thread</p>
          <p className="font-mono text-xs text-on-surface mt-1">{timeline.thread_id}</p>
        </div>
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase">Status</p>
          <p className="font-mono text-xs text-primary mt-1 uppercase">{timeline.status.replace(/_/g, ' ')}</p>
        </div>
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase">Source</p>
          <p className="font-mono text-xs text-on-surface mt-1 uppercase">{timeline.source}</p>
        </div>
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase">Updated</p>
          <p className="font-mono text-xs text-on-surface mt-1">
            {new Date(timeline.updated_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
}
