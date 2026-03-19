import type {
  CvProfileGraphPayload,
  CvGraphPayload,
  JobTimeline,
  PortfolioSummary,
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
