import type { CvEntry, CvSkill } from '../../../types/api.types';

interface Props {
  entries: CvEntry[];
  skills: CvSkill[];
}

interface StatRowProps {
  label: string;
  value: string | number;
}

function StatRow({ label, value }: StatRowProps) {
  return (
    <div className="flex justify-between items-baseline py-1 border-b border-outline/10 last:border-0">
      <span className="font-mono text-xs text-on-muted">{label}</span>
      <span className="font-mono text-xs text-on-surface">{value}</span>
    </div>
  );
}

function groupByCategory(entries: CvEntry[]): Record<string, number> {
  return entries.reduce<Record<string, number>>((acc, e) => {
    acc[e.category] = (acc[e.category] ?? 0) + 1;
    return acc;
  }, {});
}

export function ProfileStats({ entries, skills }: Props) {
  const essentialEntries = entries.filter(e => e.essential).length;
  const essentialSkills = skills.filter(s => s.essential).length;
  const byCategory = groupByCategory(entries);

  return (
    <div className="p-4 overflow-y-auto h-full">
      <p className="font-mono text-[9px] text-primary uppercase tracking-widest mb-4">
        Profile Stats
      </p>

      <div className="mb-5">
        <p className="font-mono text-[9px] text-on-muted/60 uppercase tracking-wider mb-2">
          Entries
        </p>
        <StatRow label="Total entries" value={entries.length} />
        <StatRow label="Essential" value={essentialEntries} />
      </div>

      <div className="mb-5">
        <p className="font-mono text-[9px] text-on-muted/60 uppercase tracking-wider mb-2">
          Skills
        </p>
        <StatRow label="Total skills" value={skills.length} />
        <StatRow label="Essential" value={essentialSkills} />
      </div>

      <div>
        <p className="font-mono text-[9px] text-on-muted/60 uppercase tracking-wider mb-2">
          By category
        </p>
        {Object.entries(byCategory).map(([cat, count]) => (
          <StatRow key={cat} label={cat} value={count} />
        ))}
      </div>
    </div>
  );
}
