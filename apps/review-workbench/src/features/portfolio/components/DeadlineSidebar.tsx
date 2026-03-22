import type { PortfolioSummary } from '../../../types/api.types';

interface Props {
  data?: PortfolioSummary;
}

const DEADLINE_ITEMS = [
  { jobId: '201397', source: 'tu_berlin', label: 'TU Berlin V-67-26', dueDate: '2026-04-01', urgency: 'high' },
  { jobId: '999001', source: 'tu_berlin', label: 'TU Berlin 999001', dueDate: '2026-04-15', urgency: 'medium' },
];

function daysUntil(dateStr: string) {
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.ceil(diff / 86400000);
}

export function DeadlineSidebar({ data: _data }: Props) {
  return (
    <aside className="w-72 flex-shrink-0 border-l border-outline/20 bg-surface-container-low flex flex-col">
      <div className="px-4 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em]">Deadlines</p>
      </div>
      <div className="flex-1 overflow-y-auto py-2 space-y-2 px-3">
        {DEADLINE_ITEMS.map(item => {
          const days = daysUntil(item.dueDate);
          const color = item.urgency === 'high' ? 'text-error border-error/30' : 'text-secondary border-secondary/30';
          return (
            <div key={item.jobId} className={`border bg-surface p-3 ${color}`}>
              <p className="font-mono text-[10px] uppercase tracking-wider">{item.label}</p>
              <p className="font-mono text-xs mt-1">
                {days > 0 ? `${days}d remaining` : 'Overdue'}
              </p>
              <p className="font-mono text-[9px] text-on-muted/60 mt-0.5">{item.dueDate}</p>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
