import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function pairsFromRecord(values: Record<string, string>) {
  const entries = Object.entries(values);
  if (entries.length === 0) {
    return [{ key: '', value: '', dataType: 'string' as const }];
  }

  return entries.map(([key, value]) => ({ key, value, dataType: 'string' as const }));
}

export function recordFromPairs(values: Array<{ key: string; value: string }>): Record<string, string> {
  const result: Record<string, string> = {};

  for (const pair of values) {
    const key = pair.key.trim();
    if (!key) {
      continue;
    }

    result[key] = pair.value;
  }

  return result;
}
