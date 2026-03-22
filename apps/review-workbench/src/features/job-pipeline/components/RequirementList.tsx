import { useState } from 'react';
import type { RequirementItem as ReqType } from '../../../types/api.types';
import { RequirementItem } from './RequirementItem';
import { Button } from '../../../components/atoms/Button';

interface Props {
  requirements: ReqType[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onHover: (req: ReqType | null) => void;
  onChange: (id: string, field: 'text' | 'priority' | 'notes', value: string) => void;
  onDelete: (id: string) => void;
  onAdd: () => void;
}

export function RequirementList({ requirements, selectedId, onSelect, onHover, onChange, onDelete, onAdd }: Props) {
  const [search, setSearch] = useState('');

  const filtered = search
    ? requirements.filter(r =>
        r.text.toLowerCase().includes(search.toLowerCase()) ||
        r.priority.toLowerCase().includes(search.toLowerCase())
      )
    : requirements;

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-outline/20 space-y-1.5">
        <div className="flex items-center justify-between">
          <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">
            Extracted Reqs ({filtered.length}{search ? `/${requirements.length}` : ''})
          </p>
          <Button variant="ghost" size="sm" onClick={onAdd}>+ ADD</Button>
        </div>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter requirements…"
          className="w-full bg-transparent border-0 border-b border-outline/20 outline-none font-mono text-[10px] text-on-surface placeholder:text-on-muted/30 pb-0.5 focus:border-primary/40"
        />
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filtered.length === 0 && (
          <div className="text-center py-8">
            <p className="font-mono text-[10px] text-on-muted uppercase">
              {search ? 'NO_MATCH' : 'NO_REQUIREMENTS_EXTRACTED'}
            </p>
            {!search && <Button variant="ghost" size="sm" className="mt-3" onClick={onAdd}>+ Add Manual</Button>}
          </div>
        )}
        {filtered.map(req => (
          <RequirementItem
            key={req.id}
            req={req}
            isSelected={selectedId === req.id}
            onSelect={() => onSelect(req.id)}
            onHover={onHover}
            onChange={onChange}
            onDelete={onDelete}
          />
        ))}
      </div>
    </div>
  );
}
