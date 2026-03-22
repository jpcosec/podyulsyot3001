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

// ── Fixtures: meta ────────────────────────────────────────────────────────────
import portfolio          from "./fixtures/portfolio.json";
import timeline201397     from "./fixtures/timeline_201397.json";
import timeline999001     from "./fixtures/timeline_999001.json";
import evidenceBank       from "./fixtures/evidence_bank.json";
import profileSummary     from "./fixtures/profile_summary.json";
import packageFiles       from "./fixtures/package_files_999001.json";
import cvProfileGraph     from "./fixtures/cv_profile_graph.json";
import explorerRoot       from "./fixtures/explorer_root.json";
import editorState201397  from "./fixtures/editor_state_201397.json";
import editorState999001  from "./fixtures/editor_state_999001.json";

// ── Fixtures: views ───────────────────────────────────────────────────────────
import viewMatch201397    from "./fixtures/view_match_201397.json";
import viewMatch999001    from "./fixtures/view_match_999001.json";
import viewExtract201397  from "./fixtures/view_extract_201397.json";
import viewExtract999001  from "./fixtures/view_extract_999001.json";
import viewDocs201397     from "./fixtures/view_documents_201397.json";
import viewDocs999001     from "./fixtures/view_documents_999001.json";

// ── Fixtures: artifacts (per node per job) ────────────────────────────────────
import art_scrape_201397              from "./fixtures/artifacts_scrape_201397.json";
import art_scrape_999001              from "./fixtures/artifacts_scrape_999001.json";
import art_translate_201397           from "./fixtures/artifacts_translate_if_needed_201397.json";
import art_translate_999001           from "./fixtures/artifacts_translate_if_needed_999001.json";
import art_extract_201397             from "./fixtures/artifacts_extract_understand_201397.json";
import art_extract_999001             from "./fixtures/artifacts_extract_understand_999001.json";
import art_match_201397               from "./fixtures/artifacts_match_201397.json";
import art_match_999001               from "./fixtures/artifacts_match_999001.json";
import art_review_match_201397        from "./fixtures/artifacts_review_match_201397.json";
import art_review_match_999001        from "./fixtures/artifacts_review_match_999001.json";
import art_generate_documents_201397  from "./fixtures/artifacts_generate_documents_201397.json";
import art_generate_documents_999001  from "./fixtures/artifacts_generate_documents_999001.json";
import art_render_201397              from "./fixtures/artifacts_render_201397.json";
import art_render_999001              from "./fixtures/artifacts_render_999001.json";
import art_package_201397             from "./fixtures/artifacts_package_201397.json";
import art_package_999001             from "./fixtures/artifacts_package_999001.json";

// ─────────────────────────────────────────────────────────────────────────────

const delay = <T>(v: T, ms = 80): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), ms));

const byJob = <T>(jobId: string, a: T, b: T): T =>
  jobId === "201397" ? a : b;

// ── Artifact lookup map ───────────────────────────────────────────────────────
// Fixtures contain only { node_name, files } — source/job_id are injected by getArtifacts.

type ArtifactFixture = { node_name: string; files: ArtifactListPayload["files"] };

const ARTIFACTS: Record<string, ArtifactFixture> = {
  "201397::scrape":              art_scrape_201397             as unknown as ArtifactFixture,
  "999001::scrape":              art_scrape_999001             as unknown as ArtifactFixture,
  "201397::translate_if_needed": art_translate_201397          as unknown as ArtifactFixture,
  "999001::translate_if_needed": art_translate_999001          as unknown as ArtifactFixture,
  "201397::extract_understand":  art_extract_201397            as unknown as ArtifactFixture,
  "999001::extract_understand":  art_extract_999001            as unknown as ArtifactFixture,
  "201397::match":               art_match_201397              as unknown as ArtifactFixture,
  "999001::match":               art_match_999001              as unknown as ArtifactFixture,
  "201397::review_match":        art_review_match_201397       as unknown as ArtifactFixture,
  "999001::review_match":        art_review_match_999001       as unknown as ArtifactFixture,
  "201397::generate_documents":  art_generate_documents_201397 as unknown as ArtifactFixture,
  "999001::generate_documents":  art_generate_documents_999001 as unknown as ArtifactFixture,
  "201397::render":              art_render_201397             as unknown as ArtifactFixture,
  "999001::render":              art_render_999001             as unknown as ArtifactFixture,
  "201397::package":             art_package_201397            as unknown as ArtifactFixture,
  "999001::package":             art_package_999001            as unknown as ArtifactFixture,
};

// ── In-session state ──────────────────────────────────────────────────────────

const _docStore: Record<string, Record<string, string>> = {
  "201397": { cv: "", motivation_letter: "", application_email: "" },
  "999001": {
    cv:                (viewDocs999001 as any).documents.cv,
    motivation_letter: (viewDocs999001 as any).documents.motivation_letter,
    application_email: (viewDocs999001 as any).documents.application_email,
  },
};

const _editorStore: Record<string, Record<string, unknown>> = {};

const _activeRuns: Record<string, { run_id: string; started_at: number }> = {};

// ─────────────────────────────────────────────────────────────────────────────
// API CLIENT
// ─────────────────────────────────────────────────────────────────────────────

export const apiClient = {

  // ── /api/v2/query/ ────────────────────────────────────────────────────────

  query: {

    portfolio: {
      getSummary: (): Promise<PortfolioSummary> =>
        delay(portfolio as PortfolioSummary, 120),
    },

    profile: {
      getBaseCvGraph: (): Promise<BaseCvGraphPayload> =>
        delay({
          profile_id: "mock-profile",
          snapshot_version: "0",
          captured_on: "2026-01-01",
          nodes: [],
          edges: [],
        } as BaseCvGraphPayload, 100),

      getCvProfileGraph: (): Promise<CvProfileGraphPayload> =>
        delay(cvProfileGraph as unknown as CvProfileGraphPayload, 150),
    },

    jobs: {
      getTimeline: (_source: string, jobId: string): Promise<JobTimeline> =>
        delay(byJob(jobId, timeline201397, timeline999001) as JobTimeline, 100),

      getView: (_source: string, jobId: string, view: ViewName): Promise<ViewPayload> => {
        const source = _source;
        if (view === "match") {
          const data = byJob(jobId, viewMatch201397, viewMatch999001);
          return delay({ view: "match", source, job_id: jobId, data } as ViewPayload, 200);
        }
        if (view === "extract") {
          const data = byJob(jobId, viewExtract201397, viewExtract999001);
          return delay({ view: "extract", source, job_id: jobId, data } as ViewPayload, 200);
        }
        const stored = _docStore[jobId] ?? {};
        const base = byJob(jobId, viewDocs201397 as any, viewDocs999001 as any);
        const data = {
          ...base,
          documents: {
            cv:                stored.cv                ?? base.documents.cv,
            motivation_letter: stored.motivation_letter ?? base.documents.motivation_letter,
            application_email: stored.application_email ?? base.documents.application_email,
          },
        };
        return delay({ view: "documents", source, job_id: jobId, data } as ViewPayload, 200);
      },

      getArtifacts: (_source: string, jobId: string, nodeName: string): Promise<ArtifactListPayload> => {
        const key = `${jobId}::${nodeName}`;
        const fixture = ARTIFACTS[key] ?? { node_name: nodeName, files: [] };
        return delay({
          source:    _source,
          job_id:    jobId,
          node_name: fixture.node_name,
          files:     fixture.files,
        }, 150);
      },

      getEditorState: (
        _source: string,
        jobId: string,
        nodeName: string,
      ): Promise<{ source: string; job_id: string; node_name: string; state: Record<string, unknown> }> => {
        const cached = _editorStore[`${jobId}::${nodeName}`];
        const raw = byJob(jobId, editorState201397 as any, editorState999001 as any);
        return delay({
          source: _source,
          job_id: jobId,
          node_name: nodeName,
          state: cached ?? raw?.state ?? {},
        }, 120);
      },

      getEvidenceBank: (_source: string, jobId: string): Promise<EvidenceBankPayload> =>
        delay({ ...evidenceBank, job_id: jobId } as EvidenceBankPayload, 100),

      getProfileSummary: (source: string, jobId: string): Promise<ProfileSummary> =>
        delay({ ...profileSummary, source, job_id: jobId } as ProfileSummary, 80),

      getPackageFiles: (_source: string, jobId: string): Promise<PackageFilesPayload> =>
        delay({ ...packageFiles, job_id: jobId } as PackageFilesPayload, 100),
    },

    explorer: {
      browse: (path: string = ""): Promise<ExplorerPayload> => {
        if (!path) return delay(explorerRoot as ExplorerPayload, 100);
        if (path === "tu_berlin") return delay({
          path, is_dir: true,
          entries: [
            { name: "201397", path: "tu_berlin/201397", is_dir: true, child_count: 3 },
            { name: "999001", path: "tu_berlin/999001", is_dir: true, child_count: 3 },
            { name: "index.json", path: "tu_berlin/index.json", is_dir: false, extension: "json" },
          ],
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/index.json") return delay({
          path, is_dir: false, extension: "json", content_type: "text",
          content: '{"source":"tu_berlin","jobs":["201397","999001"],"updated_at":"2026-03-22"}',
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397") return delay({
          path, is_dir: true,
          entries: [
            { name: "nodes", path: "tu_berlin/201397/nodes", is_dir: true, child_count: 2 },
            { name: "raw", path: "tu_berlin/201397/raw", is_dir: true, child_count: 1 },
            { name: "meta.json", path: "tu_berlin/201397/meta.json", is_dir: false, extension: "json" },
          ],
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/meta.json") return delay({
          path, is_dir: false, extension: "json", content_type: "text",
          content: '{"source":"tu_berlin","job_id":"201397","status":"pending_hitl"}',
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/raw") return delay({
          path, is_dir: true,
          entries: [
            { name: "source_text.md", path: "tu_berlin/201397/raw/source_text.md", is_dir: false, extension: "md" },
          ],
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/raw/source_text.md") return delay({
          path, is_dir: false, extension: "md", content_type: "text",
          content: "# Job Posting — TU Berlin\n\nPosition in Computer Science department.",
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/nodes") return delay({
          path, is_dir: true,
          entries: [
            { name: "match", path: "tu_berlin/201397/nodes/match", is_dir: true, child_count: 1 },
            { name: "scrape", path: "tu_berlin/201397/nodes/scrape", is_dir: true, child_count: 1 },
          ],
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/nodes/match") return delay({
          path, is_dir: true,
          entries: [
            { name: "approved", path: "tu_berlin/201397/nodes/match/approved", is_dir: true, child_count: 1 },
          ],
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/nodes/match/approved") return delay({
          path, is_dir: true,
          entries: [
            { name: "state.json", path: "tu_berlin/201397/nodes/match/approved/state.json", is_dir: false, extension: "json" },
          ],
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/201397/nodes/match/approved/state.json") return delay({
          path, is_dir: false, extension: "json", content_type: "text",
          content: '{"nodes":[],"edges":[],"decision":"approved"}',
        } as ExplorerPayload, 100);
        if (path === "tu_berlin/999001") return delay({
          path, is_dir: true,
          entries: [
            { name: "nodes", path: "tu_berlin/999001/nodes", is_dir: true, child_count: 5 },
            { name: "raw", path: "tu_berlin/999001/raw", is_dir: true, child_count: 1 },
            { name: "meta.json", path: "tu_berlin/999001/meta.json", is_dir: false, extension: "json" },
          ],
        } as ExplorerPayload, 100);
        return delay({ path, is_dir: true, entries: [] } as ExplorerPayload, 100);
      },
    },

  },

  // ── /api/v2/commands/ ─────────────────────────────────────────────────────

  commands: {

    jobs: {
      scrape: (_payload: ScrapeJobPayload): Promise<RunResponse> => {
        const run_id = `run_${Date.now()}`;
        console.info("[Mock] scrape →", _payload.url);
        return delay({ run_id, status: "accepted" } as RunResponse, 800);
      },

      run: (
        _source: string,
        jobId: string,
        _payload: { target_node?: string; resume_from_hitl?: boolean } = {},
      ): Promise<RunResponse> => {
        const run_id = `run_${Date.now()}`;
        _activeRuns[jobId] = { run_id, started_at: Date.now() };
        console.info("[Mock] run →", jobId, _payload);
        return delay({ run_id, status: "accepted" } as RunResponse, 800);
      },

      decideGate: (
        _source: string,
        jobId: string,
        gateName: string,
        payload: GateDecisionPayload,
      ): Promise<CommandResponse> => {
        console.info(`[Mock] gate '${gateName}' on ${jobId} → ${payload.decision}`);
        if (payload.feedback?.length) console.info("  feedback:", payload.feedback);
        return delay({ success: true, message: `${gateName}: ${payload.decision}` }, 600);
      },

      saveEditorState: (
        _source: string,
        jobId: string,
        nodeName: string,
        stateData: Record<string, unknown>,
      ): Promise<CommandResponse> => {
        _editorStore[`${jobId}::${nodeName}`] = stateData;
        return delay({ success: true }, 300);
      },

      saveDocument: (
        _source: string,
        jobId: string,
        docKey: string,
        markdown: string,
      ): Promise<CommandResponse> => {
        if (!_docStore[jobId]) _docStore[jobId] = {};
        _docStore[jobId][docKey] = markdown;
        return delay({ success: true }, 300);
      },

      archive: (
        _source: string,
        jobId: string,
        _payload: { compress_to_minio: boolean },
      ): Promise<CommandResponse> =>
        delay({ success: true, message: `${jobId} archived` }, 1200),

      delete: (_source: string, _jobId: string): Promise<CommandResponse> =>
        delay({ success: true }, 500),
    },

    profile: {
      saveCvProfileGraph: (payload: CvProfileGraphPayload): Promise<CvProfileGraphPayload> =>
        delay(payload, 400),
    },

    explorer: {
      saveFile: (_path: string, _content: string): Promise<CommandResponse> =>
        delay({ success: true }, 300),
    },

  },

  // ── /api/v2/system/ ───────────────────────────────────────────────────────

  system: {

    orchestration: {
      getThreadStatus: (_source: string, jobId: string): Promise<ThreadStatus> => {
        const run = _activeRuns[jobId];
        const isActive = run != null && Date.now() - run.started_at < 30_000;
        const tl = byJob(jobId, timeline201397, timeline999001) as any;
        return delay({
          thread_id:    tl.thread_id,
          is_active:    isActive,
          current_node: isActive ? "running…" : tl.current_node,
          pending_tasks: [],
          last_updated: new Date().toISOString(),
        } as ThreadStatus, 80);
      },

      getTrace: (_source: string, _jobId: string): Promise<TraceInfo> =>
        delay({
          run_id:        "mock-run-001",
          project_name:  "phd2-dev",
          langsmith_url: "https://smith.langchain.com/o/mock/projects/p/mock",
          total_tokens:  12340,
          latency_ms:    4200,
        } as TraceInfo, 120),
    },

    scrapers: {
      getRoadmap: (): Promise<ScraperRoadmap> =>
        delay({
          adapters: [
            { id: "tu_berlin", name: "TU Berlin Job Portal", is_healthy: true, last_successful_run: "2026-03-21T09:15:00Z", capabilities: ["html_static", "pagination"] },
            { id: "stepstone", name: "Stepstone",            is_healthy: true, last_successful_run: "2026-03-20T18:00:00Z", capabilities: ["js_rendering", "playwright"] },
            { id: "generic",   name: "Generic HTTP",         is_healthy: true, last_successful_run: "2026-03-22T07:00:00Z", capabilities: ["html_static"] },
          ],
        } as ScraperRoadmap, 150),
    },

    neo4j: {
      sync: (_source: string, _jobId: string): Promise<CommandResponse> =>
        delay({ success: true, message: "Synced to Neo4j (mock)" }, 1000),
    },

  },

} as const;
