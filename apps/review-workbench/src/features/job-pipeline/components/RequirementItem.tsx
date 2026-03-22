import { useState } from 'react';
import { cn } from '../../../utils/cn';
import type { RequirementItem as RequirementItemType } from '../../../types/api.types';

interface Props {
  req: RequirementItemType;
  isSelected: boolean;
  onSelect: () => void;
  onHover: (req: RequirementItemType | null) => void;
  onChange: (id: string, field: 'text' | 'priority' | 'notes', value: string) => void;
  onDelete: (id: string) => void;
}

const PRIORITY_STYLES = {
  must: 'bg-secondary/10 text-secondary border border-secondary/30',
  nice: 'bg-outline/10 text-on-muted border border-outline/30',
};

export function RequirementItem({ req, isSelected, onSelect, onHover, onChange, onDelete }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);

  const priorityStyle = PRIORITY_STYLES[req.priority as keyof typeof PRIORITY_STYLES] ?? PRIORITY_STYLES.nice;

  return (
    <div
      className={cn(
        'border border-outline/20 cursor-pointer transition-colors',
        isSelected ? 'border-primary/50 bg-primary/5' : 'hover:border-outline/40'
      )}
      onMouseEnter={() => onHover(req)}
      onMouseLeave={() => onHover(null)}
    >
      {/* Collapsed header — always visible */}
      <div
        className="flex items-center gap-2 px-3 py-2"
        onClick={() => { setExpanded(v => !v); onSelect(); }}
      >
        <span className={cn('font-mono text-[9px] px-1.5 py-0.5 uppercase', priorityStyle)}>
          {req.priority}
        </span>
        <span className="font-mono text-[9px] text-primary/50 flex-shrink-0">{req.id.slice(-6)}</span>
        <p className={cn(
          'font-body text-xs text-on-surface flex-1 min-w-0',
          !expanded && 'truncate'
        )}>
          {req.text}
        </p>
        <span className="font-mono text-[9px] text-on-muted/40 flex-shrink-0">{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Expanded panel */}
      {expanded && (
        <div
          className="border-t border-outline/20 px-3 py-3 space-y-3 bg-surface-low"
          onClick={e => e.stopPropagation()}
        >
          {/* Priority select */}
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] text-on-muted w-16">Priority</span>
            <select
              value={req.priority}
              onChange={e => onChange(req.id, 'priority', e.target.value)}
              className={cn(
                'font-mono text-[9px] px-1.5 py-0.5 uppercase cursor-pointer bg-transparent border-0 outline-none',
                priorityStyle
              )}
            >
              <option value="must">MUST</option>
              <option value="nice">NICE</option>
            </select>
          </div>

          {/* Text editor */}
          <div>
            <span className="font-mono text-[9px] text-on-muted block mb-1">Text</span>
            {editing ? (
              <textarea
                autoFocus
                value={req.text}
                onChange={e => onChange(req.id, 'text', e.target.value)}
                onBlur={() => setEditing(false)}
                className="w-full bg-surface border border-primary/30 p-2 font-body text-xs text-on-surface resize-none focus:outline-none focus:border-primary/60"
                rows={3}
              />
            ) : (
              <p
                className="font-body text-xs text-on-surface leading-relaxed p-2 border border-outline/20 bg-surface cursor-text"
                onDoubleClick={() => setEditing(true)}
                title="Double-click to edit"
              >
                {req.text}
              </p>
            )}
          </div>

          {/* Notes textarea */}
          <div>
            <span className="font-mono text-[9px] text-on-muted block mb-1">Notes</span>
            <textarea
              value={req.notes ?? ''}
              onChange={e => onChange(req.id, 'notes', e.target.value)}
              placeholder="Operator annotations…"
              className="w-full bg-surface-low border border-outline/20 p-2 font-mono text-[10px] text-on-surface resize-none focus:outline-none focus:border-outline/40 placeholder:text-on-muted/30"
              rows={2}
            />
          </div>

          {/* Char span info */}
          {req.char_start != null && req.char_end != null && (
            <p className="font-mono text-[9px] text-on-muted/50">
              char {req.char_start}–{req.char_end}
            </p>
          )}

          {/* Delete */}
          <button
            onClick={() => onDelete(req.id)}
            className="font-mono text-[9px] text-error/60 hover:text-error"
          >
            ✕ Delete
          </button>
        </div>
      )}
    </div>
  );
}
