import { Handle, Position } from '@xyflow/react';
import { cn } from '../../../utils/cn';
import type { CvEntry } from '../../../types/api.types';

interface EntryNodeData {
  entry: CvEntry;
  selected: boolean;
  onSelect?: (id: string, type: 'entry' | 'skill') => void;
}

interface Props {
  data: EntryNodeData;
  selected?: boolean;
}

const CATEGORY_BORDER: Record<string, string> = {
  experience:      'border-l-primary',
  job_experience:  'border-l-primary',
  education:       'border-l-outline',
  publication:     'border-l-secondary',
  language:        'border-l-error',
  language_fact:   'border-l-error',
};

function categoryBorder(category: string): string {
  return CATEGORY_BORDER[category] ?? 'border-l-outline/40';
}

function firstFieldValue(fields: Record<string, unknown>): string {
  const vals = Object.values(fields);
  const first = vals[0];
  if (typeof first === 'string') return first;
  if (typeof first === 'number' || typeof first === 'boolean') return String(first);
  return '';
}

function secondFieldValue(fields: Record<string, unknown>): string | null {
  const vals = Object.values(fields);
  if (vals.length < 2) return null;
  const second = vals[1];
  if (typeof second === 'string') return second;
  if (typeof second === 'number' || typeof second === 'boolean') return String(second);
  return null;
}

export function EntryNode({ data, selected: propSelected }: Props) {
  const { entry, selected: dataSelected, onSelect } = data;
  const isSelected = propSelected || dataSelected;
  const title = firstFieldValue(entry.fields) || entry.id;
  const sub = secondFieldValue(entry.fields);

  return (
    <div
      style={{ width: 280 }}
      onClick={() => onSelect?.(entry.id, 'entry')}
      className={cn(
        'bg-surface-container border border-outline/30 border-l-4 px-3 py-2 relative',
        categoryBorder(entry.category),
        isSelected && 'ring-1 ring-primary/60 shadow-[0_0_8px_rgba(0,242,255,0.25)]'
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-primary !border-primary/50 !w-2 !h-2"
      />

      {entry.essential && (
        <span className="absolute top-1.5 right-2 text-[10px] text-green-400 leading-none">●</span>
      )}

      <p className="font-headline font-semibold text-sm text-on-surface leading-tight pr-4 truncate">
        {title}
      </p>
      {sub && (
        <p className="text-xs text-on-muted mt-0.5 truncate">{sub}</p>
      )}
      <p className="font-mono text-[9px] text-on-muted/60 mt-1 truncate">{entry.id}</p>

      <Handle
        type="source"
        position={Position.Right}
        className="!bg-primary !border-primary/50 !w-2 !h-2"
      />
    </div>
  );
}
