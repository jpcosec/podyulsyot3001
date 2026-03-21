import type {
  CvProfileGraphPayload,
  EvidenceBankPayload,
  ExplorerPayload,
  JobTimeline,
  PackageFilesPayload,
  PortfolioSummary,
  ProfileSummary,
  StageOutputsPayload,
  ViewOnePayload,
  ViewThreePayload,
  ViewTwoPayload,
} from "../types/models";

import portfolio        from "./fixtures/portfolio.json";
import timeline201397   from "./fixtures/timeline_201397.json";
import timeline999001   from "./fixtures/timeline_999001.json";
import view1_201397     from "./fixtures/view1_201397.json";
import view1_999001     from "./fixtures/view1_999001.json";
import view2_201397     from "./fixtures/view2_201397.json";
import view2_999001     from "./fixtures/view2_999001.json";
import view3_999001     from "./fixtures/view3_999001.json";
import stageOut201397   from "./fixtures/stage_outputs_201397.json";
import stageOut999001   from "./fixtures/stage_outputs_999001.json";
import editorState201397 from "./fixtures/editor_state_201397.json";
import editorState999001 from "./fixtures/editor_state_999001.json";
import evidenceBank     from "./fixtures/evidence_bank.json";
import profileSummary   from "./fixtures/profile_summary.json";
import packageFiles     from "./fixtures/package_files_999001.json";
import cvProfileGraph   from "./fixtures/cv_profile_graph.json";
import explorerRoot     from "./fixtures/explorer_root.json";

const delay = <T>(v: T): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), 80));

// ── Portfolio ──────────────────────────────────────────────────────────────

export const getPortfolioSummary = (): Promise<PortfolioSummary> =>
  delay(portfolio as PortfolioSummary);

// ── Job timeline ───────────────────────────────────────────────────────────

export const getJobTimeline = (_source: string, jobId: string): Promise<JobTimeline> =>
  delay((jobId === "201397" ? timeline201397 : timeline999001) as JobTimeline);

// ── Views ──────────────────────────────────────────────────────────────────

export const getViewOnePayload = (_source: string, jobId: string): Promise<ViewOnePayload> =>
  delay((jobId === "201397" ? view1_201397 : view1_999001) as ViewOnePayload);

export const getViewTwoPayload = (_source: string, jobId: string): Promise<ViewTwoPayload> =>
  delay((jobId === "201397" ? view2_201397 : view2_999001) as ViewTwoPayload);

export const getViewThreePayload = (_source: string, _jobId: string): Promise<ViewThreePayload> =>
  delay(view3_999001 as ViewThreePayload);

// ── Stage outputs ──────────────────────────────────────────────────────────

export const getStageOutputs = (_source: string, jobId: string, _stage: string): Promise<StageOutputsPayload> =>
  delay((jobId === "201397" ? stageOut201397 : stageOut999001) as StageOutputsPayload);

// ── Editor state ───────────────────────────────────────────────────────────

type EditorState = { source: string; job_id: string; node_name: string; artifact_ref: string; state: Record<string, unknown> };

export const getEditorState = (_source: string, jobId: string, _nodeName: string): Promise<EditorState> =>
  delay((jobId === "201397" ? editorState201397 : editorState999001) as EditorState);

export const saveEditorState = (_source: string, jobId: string, nodeName: string, payload: Record<string, unknown>): Promise<EditorState> =>
  delay({ source: _source, job_id: jobId, node_name: nodeName, artifact_ref: "mock", state: payload });

// ── Documents ─────────────────────────────────────────────────────────────

type DocResponse = { source: string; job_id: string; doc_key: string; artifact_ref: string; content: string };

export const getDocument = (source: string, jobId: string, docKey: string): Promise<DocResponse> => {
  const docs = view3_999001.documents as Record<string, string>;
  return delay({ source, job_id: jobId, doc_key: docKey, artifact_ref: "mock", content: docs[docKey] ?? "" });
};

export const saveDocument = (source: string, jobId: string, docKey: string, content: string): Promise<DocResponse> =>
  delay({ source, job_id: jobId, doc_key: docKey, artifact_ref: "mock", content });

// ── CV graph ───────────────────────────────────────────────────────────────

export const getCvProfileGraphPayload = (): Promise<CvProfileGraphPayload> =>
  delay(cvProfileGraph as unknown as CvProfileGraphPayload);

export const saveCvProfileGraphPayload = (payload: CvProfileGraphPayload): Promise<CvProfileGraphPayload> =>
  delay(payload);

export const getBaseCvGraphPayload = () =>
  delay({ profile_id: "mock", snapshot_version: "0", captured_on: "2026-01-01", nodes: [], edges: [] });

// ── Sidebar ────────────────────────────────────────────────────────────────

export const getEvidenceBank = (_source: string, _jobId: string): Promise<EvidenceBankPayload> =>
  delay(evidenceBank as EvidenceBankPayload);

export const getProfileSummary = (source: string, jobId: string): Promise<ProfileSummary> =>
  delay({ ...profileSummary, source, job_id: jobId } as ProfileSummary);

// ── Deployment ─────────────────────────────────────────────────────────────

export const getPackageFiles = (_source: string, _jobId: string): Promise<PackageFilesPayload> =>
  delay(packageFiles as PackageFilesPayload);

// ── Explorer ───────────────────────────────────────────────────────────────

export const browseExplorer = (path: string = ""): Promise<ExplorerPayload> => {
  if (!path) return delay(explorerRoot as ExplorerPayload);
  if (path === "tu_berlin") return delay({
    path,
    is_dir: true,
    entries: [
      { name: "201397", path: "tu_berlin/201397", is_dir: true, child_count: 4 },
      { name: "999001", path: "tu_berlin/999001", is_dir: true, child_count: 6 },
    ],
  } as ExplorerPayload);
  return delay({ path, is_dir: true, entries: [] } as ExplorerPayload);
};
