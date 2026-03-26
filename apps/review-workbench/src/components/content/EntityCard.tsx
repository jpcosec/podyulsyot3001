import type { EntityCardProps } from "./types";

function getBorderColor(visualToken?: string): string | undefined {
  if (!visualToken) {
    return undefined;
  }

  if (visualToken.includes("var(--")) {
    return visualToken;
  }

  return `var(--${visualToken})`;
}

export function EntityCard({
  title,
  category,
  properties,
  badges,
  visualToken,
}: EntityCardProps) {
  const entries = Object.entries(properties ?? {});

  return (
    <div
      className="min-w-[200px] rounded-md border bg-card p-3 text-card-foreground"
      style={{ borderLeft: `3px solid ${getBorderColor(visualToken) ?? "var(--border)"}` }}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-tight">{title}</p>
        <span className="rounded border px-1.5 py-0.5 text-[10px] font-mono uppercase text-muted-foreground">
          {category}
        </span>
      </div>

      {badges && badges.length > 0 ? (
        <div className="mb-2 flex flex-wrap gap-1">
          {badges.map((badge) => (
            <span
              key={badge}
              className="rounded bg-secondary px-1.5 py-0.5 text-[10px] text-secondary-foreground"
            >
              {badge}
            </span>
          ))}
        </div>
      ) : null}

      {entries.length > 0 ? (
        <div className="space-y-1 text-xs text-muted-foreground">
          {entries.slice(0, 3).map(([key, value]) => (
            <div key={key} className="truncate">
              <span className="font-mono text-[10px]">{key}:</span> {value}
            </div>
          ))}
          {entries.length > 3 ? <div className="text-[10px]">+{entries.length - 3} more</div> : null}
        </div>
      ) : null}
    </div>
  );
}
