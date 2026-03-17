import type { StageStatus } from "../types/models";

const CLASS_BY_STATUS: Record<StageStatus, string> = {
  pending: "badge badge-pending",
  running: "badge badge-running",
  paused_review: "badge badge-paused",
  completed: "badge badge-completed",
  failed: "badge badge-failed",
};

export function StageStatusBadge({ status }: { status: StageStatus }): JSX.Element {
  return <span className={CLASS_BY_STATUS[status]}>{status.replace("_", " ")}</span>;
}
