import { useState } from 'react';
import { cn } from '../../../utils/cn';
import type { RequirementItem as RequirementItemType } from '../../../types/api.types';

interface Props {
  req: RequirementItemType;
  isSelected: boolean;
  onSelect: () => void;
  onHover: (req: RequirementItemType | null) => void;
  onChange: (id: string, field: 'text' | 'priority', value: string) => void;
  onDelete: (id: string) => void;
}

const PRIORITY_STYLES = {
  must: 'bg-secondary/10 text-secondary border border-secondary/30',
  nice: 'bg-outline/10 text-on-muted border border-outline/30',
};

export function RequirementItem({ req, isSelected, onSelect, onHover, onChange, onDelete }: Props) {
  const [editing, setEditing] = useState(false);

  return (
    <div
      className={cn(
        'border border-outline/20 p-3 cursor-pointer transition-colors',
        isSelected ? 'border-primary/50 bg-primary/5' : 'hover:border-outline/40'
      )}
      onClick={onSelect}
      onMouseEnter={() => onHover(req)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="flex items-start gap-2 mb-2">
        <span className="font-mono text-[9px] text-primary/60 mt-0.5">{req.id}</span>
        <select
          value={req.priority}
          onChange={e => onChange(req.id, 'priority', e.target.value)}
          onClick={e => e.stopPropagation()}
          className={cn(
            'font-mono text-[9px] px-1.5 py-0.5 uppercase cursor-pointer bg-transparent border-0 outline-none',
            PRIORITY_STYLES[req.priority as keyof typeof PRIORITY_STYLES] ?? PRIORITY_STYLES.nice
          )}
        >
          <option value="must">MUST</option>
          <option value="nice">NICE</option>
        </select>
        <button
          onClick={e => { e.stopPropagation(); onDelete(req.id); }}
          className="ml-auto font-mono text-[9px] text-error/60 hover:text-error px-1"
        >
          ✕
        </button>
      </div>

      {editing ? (
        <textarea
          autoFocus
          value={req.text}
          onChange={e => onChange(req.id, 'text', e.target.value)}
          onBlur={() => setEditing(false)}
          onClick={e => e.stopPropagation()}
          className="w-full bg-surface-low border border-primary/30 p-1 font-body text-sm text-on-surface resize-none focus:outline-none focus:border-primary/60"
          rows={3}
        />
      ) : (
        <p
          className="font-body text-sm text-on-surface leading-relaxed"
          onDoubleClick={e => { e.stopPropagation(); setEditing(true); }}
          title="Double-click to edit"
        >
          {req.text}
        </p>
      )}

      {req.spans.length > 0 && (
        <p className="font-mono text-[9px] text-on-muted mt-1">{req.spans.length} span(s)</p>
      )}
    </div>
  );
}
