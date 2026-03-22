import type {
  ArtifactListPayload,
  BaseCvGraphPayload,
  CommandResponse,
  CvProfileGraphPayload,
  EvidenceBankPayload,
  ExplorerPayload,
  GateDecisionPayload,
  JobTimeline,
  PackageFilesPayload,
  PortfolioSummary,
  ProfileSummary,
  RunResponse,
  ScraperRoadmap,
  ScrapeJobPayload,
  ThreadStatus,
  TraceInfo,
  ViewName,
  ViewPayload,
} from "../types/api.types";
import { apiClient as _mockClient } from "../mock/client";

const BASE = import.meta.env.VITE_REVIEW_API_BASE ?? "http://127.0.0.1:8010";
const V2 = `${BASE}/api/v2`;

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${V2}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${V2}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`PUT ${path} → ${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${V2}${path}`, {
    method: "POST",
    headers: body != null ? { "Content-Type": "application/json" } : {},
    body: body != null ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`POST ${path} → ${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${V2}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ─────────────────────────────────────────────────────────────────────────────

const _realClient = {

  query: {

    portfolio: {
      getSummary: () =>
        get<PortfolioSummary>("/query/portfolio/summary"),
    },

    profile: {
      getBaseCvGraph: () =>
        get<BaseCvGraphPayload>("/query/profile/base-cv-graph"),

      getCvProfileGraph: () =>
        get<CvProfileGraphPayload>("/query/profile/cv-profile-graph"),
    },

    jobs: {
      getTimeline: (source: string, jobId: string) =>
        get<JobTimeline>(`/query/jobs/${source}/${jobId}/timeline`),

      getView: (source: string, jobId: string, view: ViewName) =>
        get<ViewPayload>(`/query/jobs/${source}/${jobId}/views/${view}`),

      getArtifacts: (source: string, jobId: string, nodeName: string) =>
        get<ArtifactListPayload>(`/query/jobs/${source}/${jobId}/artifacts/${nodeName}`),

      getEditorState: (source: string, jobId: string, nodeName: string) =>
        get<{ source: string; job_id: string; node_name: string; state: Record<string, unknown> }>(
          `/query/jobs/${source}/${jobId}/editor/${nodeName}/state`
        ),

      getEvidenceBank: (source: string, jobId: string) =>
        get<EvidenceBankPayload>(`/query/jobs/${source}/${jobId}/evidence-bank`),

      getProfileSummary: (source: string, jobId: string) =>
        get<ProfileSummary>(`/query/jobs/${source}/${jobId}/profile/summary`),

      getPackageFiles: (source: string, jobId: string) =>
        get<PackageFilesPayload>(`/query/jobs/${source}/${jobId}/package/files`),
    },

    explorer: {
      browse: (path = "") =>
        get<ExplorerPayload>(`/query/explorer/browse${path ? `?path=${encodeURIComponent(path)}` : ""}`),
    },

  },

  commands: {

    jobs: {
      scrape: (payload: ScrapeJobPayload) =>
        post<RunResponse>("/commands/jobs/scrape", payload),

      run: (source: string, jobId: string, payload: { target_node?: string; resume_from_hitl?: boolean } = {}) =>
        post<RunResponse>(`/commands/jobs/${source}/${jobId}/run`, payload),

      decideGate: (source: string, jobId: string, gateName: string, payload: GateDecisionPayload) =>
        post<CommandResponse>(`/commands/jobs/${source}/${jobId}/gates/${gateName}/decide`, payload),

      saveEditorState: (source: string, jobId: string, nodeName: string, stateData: Record<string, unknown>) =>
        put<CommandResponse>(`/commands/jobs/${source}/${jobId}/state/${nodeName}`, stateData),

      saveDocument: (source: string, jobId: string, docKey: string, markdown: string) =>
        put<CommandResponse>(`/commands/jobs/${source}/${jobId}/documents/${docKey}`, { markdown }),

      archive: (source: string, jobId: string, payload: { compress_to_minio: boolean }) =>
        post<CommandResponse>(`/commands/jobs/${source}/${jobId}/archive`, payload),

      delete: (source: string, jobId: string) =>
        del<CommandResponse>(`/commands/jobs/${source}/${jobId}`),
    },

    profile: {
      saveCvProfileGraph: (payload: CvProfileGraphPayload) =>
        put<CvProfileGraphPayload>("/commands/profile/cv-profile-graph", payload),
    },

    explorer: {
      saveFile: (path: string, content: string) =>
        put<CommandResponse>(`/commands/explorer/file?path=${encodeURIComponent(path)}`, { content }),
    },

  },

  system: {

    orchestration: {
      getThreadStatus: (source: string, jobId: string) =>
        get<ThreadStatus>(`/system/orchestration/threads/${source}/${jobId}`),

      getTrace: (source: string, jobId: string) =>
        get<TraceInfo>(`/system/orchestration/traces/${source}/${jobId}`),
    },

    scrapers: {
      getRoadmap: () =>
        get<ScraperRoadmap>("/system/scrapers/roadmap"),
    },

    neo4j: {
      sync: (source: string, jobId: string) =>
        post<CommandResponse>("/system/neo4j/sync", { source, job_id: jobId }),
    },

  },

} as const;

export const apiClient = import.meta.env.VITE_MOCK === "true" ? _mockClient : _realClient;
