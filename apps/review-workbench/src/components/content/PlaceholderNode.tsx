import { Skeleton } from "@/components/ui/skeleton";

import type { PlaceholderNodeProps } from "./types";

function resolveColorToken(colorToken: string): string {
  if (colorToken.includes("var(--")) {
    return colorToken;
  }

  return `var(--${colorToken}, #888)`;
}

export function PlaceholderNode({ colorToken }: PlaceholderNodeProps) {
  return (
    <div
      className="h-4 w-4 rounded-full"
      style={{ backgroundColor: resolveColorToken(colorToken) }}
    />
  );
}

export function NodeSkeleton() {
  return (
    <div className="w-[180px] rounded-lg border border-border bg-card p-3">
      <Skeleton className="mb-2 h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  );
}

export function EdgeSkeleton() {
  return (
    <div className="flex items-center gap-2">
      <Skeleton className="h-2 w-2 rounded-full" />
      <Skeleton className="h-1 w-16" />
      <Skeleton className="h-2 w-2 rounded-full" />
    </div>
  );
}
