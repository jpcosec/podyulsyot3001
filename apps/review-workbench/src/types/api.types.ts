// ─────────────────────────────────────────────────────────────────────────────
// PhD 2.0 — API v2 Contract Types
// CQRS: /query/ (read-only) | /commands/ (write/execute) | /system/ (observability)
// Storage-agnostic: shapes are valid whether data comes from disk, Neo4j, or MinIO
// ─────────────────────────────────────────────────────────────────────────────

// ── Shared primitives ────────────────────────────────────────────────────────

export type JobStatus =
  | "running"
  | "pending_hitl"
  | "completed"
  | "failed"
  | "archived";

export type StageStatus =
  | "pending"
  | "running"
  | "needs_review"
  | "approved"
  | "error";

export type GateDecision = "approve" | "request_regeneration" | "reject";

// ── Query: Portfolio ─────────────────────────────────────────────────────────

export interface JobListItem {
  source: string;
  job_id: string;
  thread_id: string;
  current_node: string;
  status: JobStatus;
  updated_at: string;
}

export interface PortfolioSummary {
  totals: {
    jobs: number;
    completed: number;
    pending_hitl: number;
    running: number;
    failed: number;
    archived: number;
  };
  jobs: JobListItem[];
}

// ── Query: Job timeline ──────────────────────────────────────────────────────

export interface StageItem {
  name: string;
  status: StageStatus;
  artifact_ref: string | null;
  updated_at: string;
}

export interface JobTimeline {
  source: string;
  job_id: string;
  thread_id: string;
  current_node: string;
  status: JobStatus;
  stages: StageItem[];
  artifacts: Record<string, string>;
  updated_at: string;
}

// ── Query: Views (discriminated union) ───────────────────────────────────────

export interface GraphNode {
  id: string;
  label: string;
  kind: string;
  score?: number;
  priority?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
  score: number | null;
  reasoning: string | null;
  evidence_id: string | null;
}

export interface TextSpanItem {
  requirement_id: string;
  start_line: number;
  end_line: number;
  text_preview: string;
}

export interface RequirementTextSpan {
  start_line: number | null;
  end_line: number | null;
  start_offset: number | null;
  end_offset: number | null;
  preview_snippet: string | null;
}

export interface RequirementItem {
  id: string;
  text: string;
  priority: string;
  spans: TextSpanItem[];
  text_span: RequirementTextSpan | null;
}

export interface MatchViewData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ExtractViewData {
  source_markdown: string;
  requirements: RequirementItem[];
}

export interface DocumentsViewData {
  documents: {
    cv: string;
    motivation_letter: string;
    application_email: string;
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export type ViewName = "match" | "extract" | "documents";

export type ViewPayload =
  | { view: "match";     source: string; job_id: string; data: MatchViewData }
  | { view: "extract";   source: string; job_id: string; data: ExtractViewData }
  | { view: "documents"; source: string; job_id: string; data: DocumentsViewData };

// ── Query: Artifacts ─────────────────────────────────────────────────────────

export type ArtifactContentType =
  | "json"
  | "markdown"
  | "text"
  | "image"
  | "binary"
  | "too_large";

export interface ArtifactFile {
  path: string;
  content_type: ArtifactContentType;
  content: string;
  editable: boolean;
}

export interface ArtifactListPayload {
  source: string;
  job_id: string;
  node_name: string;
  files: ArtifactFile[];
}

// ── Query: Profile & Evidence ─────────────────────────────────────────────────

export interface EvidenceItem {
  id: string;
  title: string;
  category: string;
  tags: string[];
  summary: string;
  source_path: string;
}

export interface EvidenceBankPayload {
  source: string;
  job_id: string;
  items: EvidenceItem[];
}

export interface ProfileSummary {
  source: string;
  job_id: string;
  skills_count: number;
  projects_count: number;
  education_count: number;
  experience_count: number;
}

// ── Query: CV Graphs ─────────────────────────────────────────────────────────

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

export interface BaseCvGraphPayload {
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

// ── Query: Package & Explorer ─────────────────────────────────────────────────

export interface PackageFile {
  name: string;
  path: string;
  size_kb: number;
}

export interface PackageFilesPayload {
  source: string;
  job_id: string;
  files: PackageFile[];
}

export interface ExplorerEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size_bytes?: number;
  extension?: string;
  child_count?: number;
}

export interface ExplorerPayload {
  path: string;
  is_dir: boolean;
  entries?: ExplorerEntry[];
  name?: string;
  extension?: string;
  size_bytes?: number;
  content_type?: "text" | "image" | "binary" | "too_large";
  content?: string | null;
}

// ── Commands: payloads ────────────────────────────────────────────────────────

export interface ScrapeJobPayload {
  url: string;
  source: string;
  adapter?: string;
}

export interface RunPipelinePayload {
  target_node?: string;
  resume_from_hitl?: boolean;
}

export interface GateDecisionPayload {
  decision: GateDecision;
  feedback?: string[];
}

export interface SaveDocumentPayload {
  markdown: string;
}

export interface ArchiveJobPayload {
  compress_to_minio: boolean;
}

// ── Commands: responses ───────────────────────────────────────────────────────

export interface RunResponse {
  run_id: string;
  status: "accepted";
}

export interface CommandResponse {
  success: boolean;
  message?: string;
}

// ── System: Orchestration ─────────────────────────────────────────────────────

export interface ThreadStatus {
  thread_id: string;
  is_active: boolean;
  current_node: string | null;
  pending_tasks: string[];
  last_updated: string;
}

export interface TraceInfo {
  run_id: string;
  project_name: string;
  langsmith_url: string;
  total_tokens: number;
  latency_ms: number;
}

// ── System: Scrapers ──────────────────────────────────────────────────────────

export interface ScraperAdapter {
  id: string;
  name: string;
  is_healthy: boolean;
  last_successful_run: string;
  capabilities: string[];
}

export interface ScraperRoadmap {
  adapters: ScraperAdapter[];
}
