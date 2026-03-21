export type StageStatus =
  | "pending"
  | "running"
  | "paused_review"
  | "completed"
  | "failed";

export interface JobListItem {
  source: string;
  job_id: string;
  thread_id: string;
  current_node: string;
  status: string;
  updated_at: string;
}

export interface StageItem {
  stage: string;
  status: StageStatus;
  artifact_ref: string | null;
}

export interface JobTimeline {
  source: string;
  job_id: string;
  thread_id: string;
  current_node: string;
  status: string;
  stages: StageItem[];
  artifacts: Record<string, string>;
  updated_at: string;
}

export interface PortfolioSummary {
  totals: {
    jobs: number;
    completed: number;
    pending_review: number;
    running: number;
    failed: number;
  };
  jobs: JobListItem[];
}

export interface TextSpanItem {
  requirement_id: string;
  start_line: number;
  end_line: number;
  text_preview: string;
}

export interface RequirementItem {
  id: string;
  text: string;
  priority: string;
  spans: TextSpanItem[];
}

export interface ViewTwoPayload {
  source: string;
  job_id: string;
  source_markdown: string;
  requirements: RequirementItem[];
}

export interface GraphNode {
  id: string;
  label: string;
  kind: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
  score: number | null;
  reasoning: string | null;
  evidence_id: string | null;
}

export interface ViewOnePayload {
  source: string;
  job_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ViewThreePayload {
  source: string;
  job_id: string;
  documents: {
    cv: string;
    motivation_letter: string;
    application_email: string;
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface StageOutputFile {
  path: string;
  content_type: string;
  content: string;
  editable: boolean;
}

export interface StageOutputsPayload {
  source: string;
  job_id: string;
  stage: string;
  node_name: string | null;
  files: StageOutputFile[];
}

export interface CvGraphNode {
  id: string;
  label: string;
  node_type: string;
  depth: number;
  main_category: string;
  subcategory: string;
  source_path: string;
  source_index: number | null;
  meta: Record<string, string>;
}

export interface CvGraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
}

export interface CvGraphPayload {
  profile_id: string;
  snapshot_version: string;
  captured_on: string;
  nodes: CvGraphNode[];
  edges: CvGraphEdge[];
}

export type DescriptionWeight =
  | "headline"
  | "primary_detail"
  | "supporting_detail"
  | "footnote";

export interface CvDescription {
  key: string;
  text: string;
  weight: DescriptionWeight;
}

export interface CvEntry {
  id: string;
  category: string;
  essential: boolean;
  fields: Record<string, unknown>;
  descriptions: CvDescription[];
}

export interface CvSkill {
  id: string;
  label: string;
  category: string;
  essential: boolean;
  level: string | null;
  meta: Record<string, unknown>;
}

export interface CvDemonstratesEdge {
  id: string;
  source: string;
  target: string;
  description_keys: string[];
}

export interface CvProfileGraphPayload {
  profile_id: string;
  snapshot_version: string;
  captured_on: string;
  entries: CvEntry[];
  skills: CvSkill[];
  demonstrates: CvDemonstratesEdge[];
}
