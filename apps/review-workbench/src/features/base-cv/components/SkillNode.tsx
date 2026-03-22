import { Handle, Position } from '@xyflow/react';
import { cn } from '../../../utils/cn';
import type { CvSkill } from '../../../types/api.types';

interface SkillNodeData {
  skill: CvSkill;
  selected: boolean;
  onSelect?: (id: string, type: 'entry' | 'skill') => void;
}

interface Props {
  data: SkillNodeData;
  selected?: boolean;
}

export function SkillNode({ data, selected: propSelected }: Props) {
  const { skill, selected: dataSelected, onSelect } = data;
  const isSelected = propSelected || dataSelected;

  return (
    <div
      style={{ width: 160 }}
      onClick={() => onSelect?.(skill.id, 'skill')}
      className={cn(
        'bg-surface-container border border-outline/30 px-2 py-1.5 relative',
        isSelected ? 'border-primary' : 'border-outline/30'
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-primary !border-primary/50 !w-2 !h-2"
      />

      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="font-body text-xs text-on-surface leading-tight truncate flex-1 min-w-0">
          {skill.label}
        </span>
        {skill.level && (
          <span className="font-mono text-[9px] text-secondary border border-secondary/40 px-1 rounded-sm shrink-0">
            {skill.level}
          </span>
        )}
      </div>
      <p className="font-mono text-[9px] text-on-muted/60 mt-0.5 truncate">{skill.category}</p>

      <Handle
        type="source"
        position={Position.Right}
        className="!bg-primary !border-primary/50 !w-2 !h-2"
      />
    </div>
  );
}
