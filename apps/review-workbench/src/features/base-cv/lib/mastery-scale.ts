export interface MasteryLevel {
  value: number;
  tag: "novice" | "beginner" | "intermediate" | "advanced" | "expert";
  label: string;
  cefrEquiv: string;
  dreyfus: string;
  intensity: number;
}

export const MASTERY_SCALE: readonly MasteryLevel[] = [
  {
    value: 1,
    tag: "novice",
    label: "Novice",
    cefrEquiv: "A1",
    dreyfus: "Novice",
    intensity: 0.17,
  },
  {
    value: 2,
    tag: "beginner",
    label: "Beginner",
    cefrEquiv: "A2",
    dreyfus: "Advanced Beginner",
    intensity: 0.33,
  },
  {
    value: 3,
    tag: "intermediate",
    label: "Intermediate",
    cefrEquiv: "B1-B2",
    dreyfus: "Competent",
    intensity: 0.5,
  },
  {
    value: 4,
    tag: "advanced",
    label: "Advanced",
    cefrEquiv: "C1",
    dreyfus: "Proficient",
    intensity: 0.75,
  },
  {
    value: 5,
    tag: "expert",
    label: "Expert",
    cefrEquiv: "C2",
    dreyfus: "Expert",
    intensity: 1,
  },
] as const;

export const CATEGORY_HUES: Readonly<Record<string, number>> = {
  programming: 210,
  machine_learning: 188,
  data_platform: 168,
  devops: 198,
  language: 270,
  soft_skill: 36,
  electronics_robotics: 345,
  uncategorized: 210,
};

const CEFR_TO_TAG: Readonly<Record<string, MasteryLevel["tag"]>> = {
  a1: "novice",
  a2: "beginner",
  b1: "intermediate",
  b2: "intermediate",
  c1: "advanced",
  c2: "expert",
};

const NORMALIZED_TO_TAG: Readonly<Record<string, MasteryLevel["tag"]>> = {
  novice: "novice",
  beginner: "beginner",
  elementary: "beginner",
  intermediate: "intermediate",
  competent: "intermediate",
  advanced: "advanced",
  proficient: "advanced",
  expert: "expert",
  mastery: "expert",
};

function toTag(value: string | null): MasteryLevel["tag"] {
  if (!value) {
    return "intermediate";
  }
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return "intermediate";
  }
  if (normalized in CEFR_TO_TAG) {
    return CEFR_TO_TAG[normalized];
  }
  if (normalized in NORMALIZED_TO_TAG) {
    return NORMALIZED_TO_TAG[normalized];
  }
  return "intermediate";
}

export function getMasteryLevel(tag: string): MasteryLevel | null {
  const normalized = tag.trim().toLowerCase();
  return MASTERY_SCALE.find((item) => item.tag === normalized) ?? null;
}

export function getMasteryByValue(value: number): MasteryLevel | null {
  return MASTERY_SCALE.find((item) => item.value === value) ?? null;
}

export function resolveMasteryLevel(
  level: string | null,
  meta: Record<string, unknown>,
): MasteryLevel {
  const explicitTag = typeof meta.mastery_tag === "string" ? meta.mastery_tag : null;
  const explicitValue = typeof meta.mastery_value === "number" ? meta.mastery_value : null;
  const byTag = explicitTag ? getMasteryLevel(explicitTag) : null;
  if (byTag) {
    return byTag;
  }
  if (explicitValue) {
    const byValue = getMasteryByValue(explicitValue);
    if (byValue) {
      return byValue;
    }
  }
  const inferred = getMasteryLevel(toTag(level));
  if (inferred) {
    return inferred;
  }
  return MASTERY_SCALE[2];
}

export function masteryIntensity(tag: string | null): number {
  const level = getMasteryLevel(tag ?? "") ?? MASTERY_SCALE[2];
  return level.intensity;
}

export function masteryColorForCategory(category: string, masteryTag: string | null): string {
  const hue = CATEGORY_HUES[category] ?? CATEGORY_HUES.uncategorized;
  const intensity = masteryIntensity(masteryTag);
  const lightness = 86 - Math.round(intensity * 56);
  return `hsl(${hue} 74% ${lightness}%)`;
}

export function nextDescriptionWeight(index: number): "headline" | "primary_detail" | "supporting_detail" | "footnote" {
  if (index <= 0) {
    return "headline";
  }
  if (index === 1) {
    return "primary_detail";
  }
  if (index < 4) {
    return "supporting_detail";
  }
  return "footnote";
}
