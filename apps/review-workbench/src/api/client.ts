import type {
  CvProfileGraphPayload,
  CvGraphPayload,
  EvidenceBankPayload,
  JobTimeline,
  PackageFilesPayload,
  PortfolioSummary,
  ProfileSummary,
  StageOutputsPayload,
  ViewOnePayload,
  ViewThreePayload,
  ViewTwoPayload,
} from "../types/models";

const API_BASE = import.meta.env.VITE_REVIEW_API_BASE ?? "http://127.0.0.1:8010";

export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  const response = await fetch(`${API_BASE}/api/v1/portfolio/summary`);
  if (!response.ok) {
    throw new Error(`portfolio summary failed: ${response.status}`);
  }
  return (await response.json()) as PortfolioSummary;
}

export async function getJobTimeline(
  source: string,
  jobId: string,
): Promise<JobTimeline> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/timeline`);
  if (!response.ok) {
    throw new Error(`job timeline failed: ${response.status}`);
  }
  return (await response.json()) as JobTimeline;
}

export async function getViewTwoPayload(
  source: string,
  jobId: string,
): Promise<ViewTwoPayload> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/view2`);
  if (!response.ok) {
    throw new Error(`view2 payload failed: ${response.status}`);
  }
  return (await response.json()) as ViewTwoPayload;
}

export async function getViewOnePayload(
  source: string,
  jobId: string,
): Promise<ViewOnePayload> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/view1`);
  if (!response.ok) {
    throw new Error(`view1 payload failed: ${response.status}`);
  }
  return (await response.json()) as ViewOnePayload;
}

export async function getViewThreePayload(
  source: string,
  jobId: string,
): Promise<ViewThreePayload> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/view3`);
  if (!response.ok) {
    throw new Error(`view3 payload failed: ${response.status}`);
  }
  return (await response.json()) as ViewThreePayload;
}

export async function getStageOutputs(
  source: string,
  jobId: string,
  stage: string,
): Promise<StageOutputsPayload> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/stage/${stage}/outputs`);
  if (!response.ok) {
    throw new Error(`stage outputs failed: ${response.status}`);
  }
  return (await response.json()) as StageOutputsPayload;
}

export async function getEditorState(
  source: string,
  jobId: string,
  nodeName: string,
): Promise<{ source: string; job_id: string; node_name: string; artifact_ref: string; state: Record<string, unknown> }> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/editor/${nodeName}/state`);
  if (!response.ok) {
    throw new Error(`editor state failed: ${response.status}`);
  }
  return (await response.json()) as {
    source: string;
    job_id: string;
    node_name: string;
    artifact_ref: string;
    state: Record<string, unknown>;
  };
}

export async function saveEditorState(
  source: string,
  jobId: string,
  nodeName: string,
  payload: Record<string, unknown>,
): Promise<{ source: string; job_id: string; node_name: string; artifact_ref: string; state: Record<string, unknown> }> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/editor/${nodeName}/state`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`save editor state failed: ${response.status} ${detail}`);
  }
  return (await response.json()) as {
    source: string;
    job_id: string;
    node_name: string;
    artifact_ref: string;
    state: Record<string, unknown>;
  };
}

export async function getDocument(
  source: string,
  jobId: string,
  docKey: string,
): Promise<{ source: string; job_id: string; doc_key: string; artifact_ref: string; content: string }> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/documents/${docKey}`);
  if (!response.ok) {
    throw new Error(`document load failed: ${response.status}`);
  }
  return (await response.json()) as {
    source: string;
    job_id: string;
    doc_key: string;
    artifact_ref: string;
    content: string;
  };
}

export async function saveDocument(
  source: string,
  jobId: string,
  docKey: string,
  content: string,
): Promise<{ source: string; job_id: string; doc_key: string; artifact_ref: string; content: string }> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/documents/${docKey}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`document save failed: ${response.status} ${detail}`);
  }
  return (await response.json()) as {
    source: string;
    job_id: string;
    doc_key: string;
    artifact_ref: string;
    content: string;
  };
}

export async function getBaseCvGraphPayload(): Promise<CvGraphPayload> {
  const response = await fetch(`${API_BASE}/api/v1/portfolio/base-cv-graph`);
  if (!response.ok) {
    throw new Error(`base cv graph payload failed: ${response.status}`);
  }
  return (await response.json()) as CvGraphPayload;
}

export async function getCvProfileGraphPayload(): Promise<CvProfileGraphPayload> {
  const response = await fetch(`${API_BASE}/api/v1/portfolio/cv-profile-graph`);
  if (!response.ok) {
    throw new Error(`cv profile graph payload failed: ${response.status}`);
  }
  return (await response.json()) as CvProfileGraphPayload;
}

export async function saveCvProfileGraphPayload(
  payload: CvProfileGraphPayload,
): Promise<CvProfileGraphPayload> {
  const response = await fetch(`${API_BASE}/api/v1/portfolio/cv-profile-graph`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`save cv profile graph failed: ${response.status} ${detail}`);
  }
  return (await response.json()) as CvProfileGraphPayload;
}

export async function getEvidenceBank(source: string, jobId: string): Promise<EvidenceBankPayload> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/evidence-bank`);
  if (!response.ok) {
    throw new Error(`evidence bank failed: ${response.status}`);
  }
  return (await response.json()) as EvidenceBankPayload;
}

export async function getProfileSummary(source: string, jobId: string): Promise<ProfileSummary> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/profile/summary`);
  if (!response.ok) {
    throw new Error(`profile summary failed: ${response.status}`);
  }
  return (await response.json()) as ProfileSummary;
}

export async function getPackageFiles(source: string, jobId: string): Promise<PackageFilesPayload> {
  const response = await fetch(`${API_BASE}/api/v1/jobs/${source}/${jobId}/package/files`);
  if (!response.ok) {
    throw new Error(`package files failed: ${response.status}`);
  }
  return (await response.json()) as PackageFilesPayload;
}
