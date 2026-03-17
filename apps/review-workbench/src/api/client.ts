import type {
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
