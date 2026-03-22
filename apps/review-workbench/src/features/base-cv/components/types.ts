import type { CvDescription } from '../../../types/api.types';

export type SkillShape = "circle" | "diamond" | "square";

export interface BaseGraphNodeData extends Record<string, unknown> {
  kind: "entry" | "skill" | "group";
  label: string;
}

export interface EntryNodeData extends BaseGraphNodeData {
  kind: "entry";
  category: string;
  essential: boolean;
  descriptions: CvDescription[];
  expanded: boolean;
  connectedSkillLabels: string[];
  onToggleExpand: (entryId: string) => void;
  onUpdateCategory: (entryId: string, category: string) => void;
  onToggleEssential: (entryId: string, next: boolean) => void;
  onUpdateDescription: (entryId: string, descriptionKey: string, text: string) => void;
  onAddDescription: (entryId: string) => void;
}

export interface SkillNodeData extends BaseGraphNodeData {
  kind: "skill";
  category: string;
  essential: boolean;
  fillColor: string;
  masteryTag: string;
  masteryLabel: string;
  masteryValue: number;
  masteryIntensity: number;
  shape: SkillShape;
  related: boolean;
  onSelectSkill?: (skillId: string) => void;
}

export interface GroupNodeData extends BaseGraphNodeData {
  kind: "group";
  category: string;
  count: number;
  countLabel: string;
  expanded: boolean;
  addLabel: string;
  isDropzoneActive: boolean;
  onToggleGroup: (category: string) => void;
  onAddItem: (category: string) => void;
  onSelectGroup?: (category: string) => void;
}

export type CvGraphNodeData = EntryNodeData | SkillNodeData | GroupNodeData;
