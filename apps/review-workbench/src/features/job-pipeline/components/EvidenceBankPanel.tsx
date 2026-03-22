import type { EvidenceItem } from '../../../types/api.types';

interface Props {
  items: EvidenceItem[];
}

export function EvidenceBankPanel({ items }: Props) {
  return (
    <div className="w-64 bg-background border-r border-primary/10 flex flex-col overflow-hidden">
      <div className="px-3 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">Assets Repo</p>
      </div>
      <div className="flex-1 overflow-y-auto py-2 space-y-2 px-2">
        {items.map(item => (
          <div
            key={item.id}
            className="bg-surface-container border border-primary/10 hover:border-primary/40 p-2 cursor-grab transition-colors"
            title={item.summary}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono text-[9px] text-primary/60 uppercase">{item.id}</span>
            </div>
            <p className="font-body text-xs text-on-surface leading-tight line-clamp-2">{item.title}</p>
            <div className="flex flex-wrap gap-1 mt-1">
              {item.tags.slice(0, 2).map(tag => (
                <span key={tag} className="font-mono text-[8px] text-on-muted border border-outline/30 px-1">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
