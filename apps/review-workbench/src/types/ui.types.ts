// ─────────────────────────────────────────────────────────────────────────────
// PhD 2.0 — Internal UI State Types
// These are frontend-only types for component state, editor state, and UI interactions.
// API contract types live in api.types.ts
// ─────────────────────────────────────────────────────────────────────────────

// ── ReactFlow / Match Graph ───────────────────────────────────────────────────

export interface MatchNodeData {
  label: string;
  kind: 'requirement' | 'profile';
  score?: number;
  priority?: string;
  status?: 'resolved' | 'unresolved' | 'gap';
}

export interface MatchEdgeData {
  score: number | null;
  reasoning: string | null;
  edgeType: 'llm' | 'manual';
}

// ── Extract & Understand editor state ─────────────────────────────────────────

export interface RequirementDraft {
  id: string;
  text: string;
  priority: 'must' | 'nice';
  spans: Array<{
    requirement_id: string;
    start_line: number;
    end_line: number;
    text_preview: string;
  }>;
  isDirty?: boolean;
  isNew?: boolean;
}

export interface ExtractEditorState {
  requirements: RequirementDraft[];
  selectedId: string | null;
  isDirty: boolean;
}

// ── Document editor state ──────────────────────────────────────────────────────

export type DocKey = 'cv' | 'motivation_letter' | 'application_email';

export interface DocumentDraft {
  key: DocKey;
  content: string;
  isDirty: boolean;
  isApproved: boolean;
}

export interface DocumentEditorState {
  documents: Record<DocKey, DocumentDraft>;
  activeTab: DocKey;
}

// ── Explorer UI state ──────────────────────────────────────────────────────────

export interface ExplorerTreeNode {
  name: string;
  path: string;
  isDir: boolean;
  isExpanded?: boolean;
  children?: ExplorerTreeNode[];
  childCount?: number;
}

// ── Gate decision UI ───────────────────────────────────────────────────────────

export type GateDecisionUI = 'approve' | 'request_regeneration' | 'reject';

export interface GateDecisionState {
  isOpen: boolean;
  decision: GateDecisionUI | null;
  feedback: string[];
}
