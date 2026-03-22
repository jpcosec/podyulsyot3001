import type { RequirementItem as ReqType } from '../../../types/api.types';
import { RequirementItem } from './RequirementItem';
import { Button } from '../../../components/atoms/Button';

interface Props {
  requirements: ReqType[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onHover: (req: ReqType | null) => void;
  onChange: (id: string, field: 'text' | 'priority', value: string) => void;
  onDelete: (id: string) => void;
  onAdd: () => void;
}

export function RequirementList({ requirements, selectedId, onSelect, onHover, onChange, onDelete, onAdd }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-outline/20 flex items-center justify-between">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">
          Extracted Reqs ({requirements.length})
        </p>
        <Button variant="ghost" size="sm" onClick={onAdd}>+ ADD</Button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {requirements.length === 0 && (
          <div className="text-center py-8">
            <p className="font-mono text-[10px] text-on-muted uppercase">NO_REQUIREMENTS_EXTRACTED</p>
            <Button variant="ghost" size="sm" className="mt-3" onClick={onAdd}>+ Add Manual</Button>
          </div>
        )}
        {requirements.map(req => (
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
