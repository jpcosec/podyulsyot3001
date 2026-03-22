import { cn } from '../../../utils/cn';
import type { CvSkill } from '../../../types/api.types';
import { MASTERY_SCALE, masteryColorForCategory, resolveMasteryLevel } from '../lib/mastery-scale';

interface Props {
  skills: CvSkill[];
  relatedSkillIds: Set<string>;
  selectedSkillId: string;
  focusedEntryId: string;
  onSelectSkill: (id: string) => void;
  onAddSkill: () => void;
  onSkillChange: (id: string, field: 'label' | 'level', value: string) => void;
  onToggleSkillEssential: (id: string) => void;
}

interface SkillChipProps {
  skill: CvSkill;
  isSelected: boolean;
  onSelect: () => void;
}

function SkillChip({ skill, isSelected, onSelect }: SkillChipProps) {
  const mastery = resolveMasteryLevel(skill.level, skill.meta);
  const color = masteryColorForCategory(skill.category, mastery.tag);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'flex items-center gap-1.5 px-2 py-1 font-mono text-[9px] border transition-colors text-left',
        isSelected
          ? 'border-primary/60 bg-primary/10 text-on-surface'
          : 'border-outline/20 bg-surface-high text-on-muted hover:border-outline/40 hover:text-on-surface'
      )}
    >
      <span
        className="w-2 h-2 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="truncate">{skill.label}</span>
      {skill.essential && (
        <span className="text-green-400 shrink-0">●</span>
      )}
    </button>
  );
}

interface SkillEditFormProps {
  skill: CvSkill;
  onSkillChange: (id: string, field: 'label' | 'level', value: string) => void;
  onToggleEssential: (id: string) => void;
}

function SkillEditForm({ skill, onSkillChange, onToggleEssential }: SkillEditFormProps) {
  return (
    <div className="mt-2 p-2 bg-surface-high border border-outline/20 flex flex-col gap-2">
      <div>
        <label className="block font-mono text-[9px] text-on-muted uppercase tracking-wider mb-1">
          Label
        </label>
        <input
          type="text"
          value={skill.label}
          onChange={e => onSkillChange(skill.id, 'label', e.target.value)}
          className="w-full bg-surface border border-outline/30 px-2 py-1 font-mono text-xs text-on-surface focus:outline-none focus:border-primary/60"
        />
      </div>
      <div>
        <label className="block font-mono text-[9px] text-on-muted uppercase tracking-wider mb-1">
          Level
        </label>
        <select
          value={skill.level ?? ''}
          onChange={e => onSkillChange(skill.id, 'level', e.target.value)}
          className="w-full bg-surface border border-outline/30 px-2 py-1 font-mono text-xs text-on-surface focus:outline-none focus:border-primary/60"
        >
          <option value="">— unset —</option>
          {MASTERY_SCALE.map(m => (
            <option key={m.tag} value={m.tag}>
              {m.label} ({m.value}/5)
            </option>
          ))}
        </select>
      </div>
      <button
        type="button"
        onClick={() => onToggleEssential(skill.id)}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 border text-xs font-mono transition-colors',
          skill.essential
            ? 'border-green-500/60 text-green-400 bg-green-500/10'
            : 'border-outline/30 text-on-muted bg-surface hover:border-outline/60'
        )}
      >
        <span className={skill.essential ? 'text-green-400' : 'text-on-muted/40'}>●</span>
        {skill.essential ? 'Essential' : 'Not essential'}
      </button>
    </div>
  );
}

interface SkillSectionProps {
  title: string;
  skills: CvSkill[];
  selectedSkillId: string;
  onSelectSkill: (id: string) => void;
  onSkillChange: (id: string, field: 'label' | 'level', value: string) => void;
  onToggleSkillEssential: (id: string) => void;
}

function SkillSection({
  title,
  skills,
  selectedSkillId,
  onSelectSkill,
  onSkillChange,
  onToggleSkillEssential,
}: SkillSectionProps) {
  if (skills.length === 0) return null;

  return (
    <div className="mb-3">
      <p className="font-mono text-[9px] text-on-muted uppercase tracking-widest mb-2 px-4">
        {title}
      </p>
      <div className="flex flex-col gap-1 px-3">
        {skills.map(skill => (
          <div key={skill.id}>
            <SkillChip
              skill={skill}
              isSelected={selectedSkillId === skill.id}
              onSelect={() => onSelectSkill(skill.id)}
            />
            {selectedSkillId === skill.id && (
              <SkillEditForm
                skill={skill}
                onSkillChange={onSkillChange}
                onToggleEssential={onToggleSkillEssential}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkillPalette({
  skills,
  relatedSkillIds,
  selectedSkillId,
  focusedEntryId,
  onSelectSkill,
  onAddSkill,
  onSkillChange,
  onToggleSkillEssential,
}: Props) {
  const related = skills.filter(s => relatedSkillIds.has(s.id));
  const unrelated = skills.filter(s => !relatedSkillIds.has(s.id));

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-widest px-4 py-2 border-b border-outline/20 shrink-0">
        Skills
      </p>

      <div className="flex-1 overflow-y-auto py-2">
        {focusedEntryId ? (
          <>
            <SkillSection
              title="Related"
              skills={related}
              selectedSkillId={selectedSkillId}
              onSelectSkill={onSelectSkill}
              onSkillChange={onSkillChange}
              onToggleSkillEssential={onToggleSkillEssential}
            />
            <SkillSection
              title="Unrelated"
              skills={unrelated}
              selectedSkillId={selectedSkillId}
              onSelectSkill={onSelectSkill}
              onSkillChange={onSkillChange}
              onToggleSkillEssential={onToggleSkillEssential}
            />
            {related.length === 0 && unrelated.length === 0 && (
              <p className="font-mono text-[9px] text-on-muted/60 italic px-4">No skills yet.</p>
            )}
          </>
        ) : (
          <SkillSection
            title="All Skills"
            skills={skills}
            selectedSkillId={selectedSkillId}
            onSelectSkill={onSelectSkill}
            onSkillChange={onSkillChange}
            onToggleSkillEssential={onToggleSkillEssential}
          />
        )}
      </div>

      <div className="shrink-0 border-t border-outline/20 p-3">
        <button
          type="button"
          onClick={onAddSkill}
          className="w-full text-left font-mono text-[10px] text-primary/70 hover:text-primary transition-colors"
        >
          + Add skill
        </button>
      </div>
    </div>
  );
}
