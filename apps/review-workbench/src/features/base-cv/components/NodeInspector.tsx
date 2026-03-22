import { cn } from '../../../utils/cn';
import type { CvEntry, CvSkill } from '../../../types/api.types';
import { MASTERY_SCALE, masteryColorForCategory, resolveMasteryLevel } from '../lib/mastery-scale';

interface Props {
  entryId: string | null;
  skillId: string | null;
  entries: CvEntry[];
  skills: CvSkill[];
  onEntryChange: (id: string, field: string, value: string) => void;
  onSkillChange: (id: string, field: 'label' | 'level', value: string) => void;
  onToggleEssential: (id: string, type: 'entry' | 'skill') => void;
  groupCategory: string | null;
  onMoveEntry?: (entryId: string, direction: 'up' | 'down') => void;
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

function GroupReorderPanel({
  category,
  entries,
  onMoveEntry,
}: {
  category: string;
  entries: CvEntry[];
  onMoveEntry?: (entryId: string, direction: 'up' | 'down') => void;
}) {
  const categoryEntries = entries.filter(e => e.category === category);

  return (
    <div className="p-4 overflow-y-auto h-full">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-widest mb-3 border-b border-outline/20 pb-2">
        Node Inspector
      </p>
      <p className="font-mono text-[9px] text-primary uppercase tracking-widest mb-1">
        Group: {category.replace(/_/g, ' ')}
      </p>
      <p className="font-mono text-[9px] text-on-muted/60 mb-4">
        {categoryEntries.length} entries
      </p>

      <div className="flex flex-col gap-1">
        {categoryEntries.map((entry, index) => {
          const label = (
            typeof entry.fields.role === 'string' ? entry.fields.role
            : typeof entry.fields.degree === 'string' ? entry.fields.degree
            : typeof entry.fields.title === 'string' ? entry.fields.title
            : typeof entry.fields.full_name === 'string' ? entry.fields.full_name
            : entry.id
          );
          return (
            <div
              key={entry.id}
              className="flex items-center gap-2 bg-surface-high border border-outline/20 px-2 py-1.5"
            >
              <span className="flex-1 font-mono text-[10px] text-on-surface truncate">
                {label}
              </span>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  disabled={index === 0}
                  onClick={() => onMoveEntry?.(entry.id, 'up')}
                  className="font-mono text-[10px] text-on-muted hover:text-primary disabled:opacity-30 transition-colors px-1"
                  title="Move up"
                >
                  ↑
                </button>
                <button
                  type="button"
                  disabled={index === categoryEntries.length - 1}
                  onClick={() => onMoveEntry?.(entry.id, 'down')}
                  className="font-mono text-[10px] text-on-muted hover:text-primary disabled:opacity-30 transition-colors px-1"
                  title="Move down"
                >
                  ↓
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
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
  groupCategory,
  onMoveEntry,
}: Props) {
  if (groupCategory) {
    return (
      <GroupReorderPanel
        category={groupCategory}
        entries={entries}
        onMoveEntry={onMoveEntry}
      />
    );
  }

  if (entryId) {
    const entry = entries.find(e => e.id === entryId);
    if (!entry) return null;

    const stringFields = Object.entries(entry.fields).filter(
      ([, v]) => typeof v === 'string'
    );

    return (
      <div className="p-4 overflow-y-auto h-full">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-widest mb-3 border-b border-outline/20 pb-2">
          Node Inspector
        </p>
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

    const mastery = resolveMasteryLevel(skill.level, skill.meta);
    const masteryColor = masteryColorForCategory(skill.category, mastery.tag);

    return (
      <div className="p-4 overflow-y-auto h-full">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-widest mb-3 border-b border-outline/20 pb-2">
          Node Inspector
        </p>
        <p className="font-mono text-[9px] text-primary uppercase tracking-widest mb-1">
          Skill
        </p>
        <p className="font-mono text-[9px] text-on-muted/60 mb-4 break-all">{skill.id}</p>

        <div className="mb-3">
          <label className="block font-mono text-[9px] text-on-muted uppercase tracking-wider mb-1">
            label
          </label>
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full shrink-0"
              style={{ backgroundColor: masteryColor }}
            />
            <input
              type="text"
              value={skill.label}
              onChange={e => onSkillChange(skill.id, 'label', e.target.value)}
              className={cn(
                'flex-1 bg-surface-high border border-outline/30 px-2 py-1',
                'font-mono text-xs text-on-surface',
                'focus:outline-none focus:border-primary/60'
              )}
            />
          </div>
        </div>

        <div className="mb-3">
          <label className="block font-mono text-[9px] text-on-muted uppercase tracking-wider mb-1">
            level
          </label>
          <select
            value={skill.level ?? ''}
            onChange={e => onSkillChange(skill.id, 'level', e.target.value)}
            className={cn(
              'w-full bg-surface-high border border-outline/30 px-2 py-1',
              'font-mono text-xs text-on-surface',
              'focus:outline-none focus:border-primary/60'
            )}
          >
            <option value="">— unset —</option>
            {MASTERY_SCALE.map(m => (
              <option key={m.tag} value={m.tag}>
                {m.label} ({m.value}/5)
              </option>
            ))}
          </select>
        </div>

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
