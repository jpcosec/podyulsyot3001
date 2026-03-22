import { cn } from '../../../utils/cn';
import type { CvEntry, CvSkill } from '../../../types/api.types';

interface Props {
  entryId: string | null;
  skillId: string | null;
  entries: CvEntry[];
  skills: CvSkill[];
  onEntryChange: (id: string, field: string, value: string) => void;
  onSkillChange: (id: string, field: 'label' | 'level', value: string) => void;
  onToggleEssential: (id: string, type: 'entry' | 'skill') => void;
}

function FieldInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="mb-3">
      <label className="block font-mono text-[9px] text-on-muted uppercase tracking-wider mb-1">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        className={cn(
          'w-full bg-surface-high border border-outline/30 px-2 py-1',
          'font-mono text-xs text-on-surface',
          'focus:outline-none focus:border-primary/60',
          'placeholder:text-on-muted/40'
        )}
      />
    </div>
  );
}

function EssentialToggle({
  essential,
  onToggle,
}: {
  essential: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 border text-xs font-mono',
        'transition-colors duration-150',
        essential
          ? 'border-green-500/60 text-green-400 bg-green-500/10'
          : 'border-outline/30 text-on-muted bg-surface-high hover:border-outline/60'
      )}
    >
      <span className={essential ? 'text-green-400' : 'text-on-muted/40'}>●</span>
      {essential ? 'Essential' : 'Not essential'}
    </button>
  );
}

export function NodeInspector({
  entryId,
  skillId,
  entries,
  skills,
  onEntryChange,
  onSkillChange,
  onToggleEssential,
}: Props) {
  if (entryId) {
    const entry = entries.find(e => e.id === entryId);
    if (!entry) return null;

    const stringFields = Object.entries(entry.fields).filter(
      ([, v]) => typeof v === 'string'
    );

    return (
      <div className="p-4 overflow-y-auto h-full">
        <p className="font-mono text-[9px] text-primary uppercase tracking-widest mb-1">
          Entry
        </p>
        <p className="font-headline font-semibold text-sm text-on-surface mb-0.5 break-all">
          {entry.category}
        </p>
        <p className="font-mono text-[9px] text-on-muted/60 mb-4 break-all">{entry.id}</p>

        {stringFields.map(([field, value]) => (
          <FieldInput
            key={field}
            label={field}
            value={value as string}
            onChange={v => onEntryChange(entry.id, field, v)}
          />
        ))}

        <div className="mt-4">
          <EssentialToggle
            essential={entry.essential}
            onToggle={() => onToggleEssential(entry.id, 'entry')}
          />
        </div>
      </div>
    );
  }

  if (skillId) {
    const skill = skills.find(s => s.id === skillId);
    if (!skill) return null;

    return (
      <div className="p-4 overflow-y-auto h-full">
        <p className="font-mono text-[9px] text-primary uppercase tracking-widest mb-1">
          Skill
        </p>
        <p className="font-mono text-[9px] text-on-muted/60 mb-4 break-all">{skill.id}</p>

        <FieldInput
          label="label"
          value={skill.label}
          onChange={v => onSkillChange(skill.id, 'label', v)}
        />
        <FieldInput
          label="level"
          value={skill.level ?? ''}
          onChange={v => onSkillChange(skill.id, 'level', v)}
        />

        <div className="mt-2">
          <EssentialToggle
            essential={skill.essential}
            onToggle={() => onToggleEssential(skill.id, 'skill')}
          />
        </div>
      </div>
    );
  }

  return null;
}
