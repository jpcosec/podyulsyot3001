import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getJobTimeline } from "../api/client";
import type { JobTimeline } from "../types/models";

interface PackageFile {
  name: string;
  path: string;
  size_kb: number;
  preview?: string;
}

export function DeploymentPage(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [timeline, setTimeline] = useState<JobTimeline | null>(null);
  const [packageFiles, setPackageFiles] = useState<PackageFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getJobTimeline(source, jobId)
      .then(setTimeline)
      .catch(() => setTimeline(null))
      .finally(() => setLoading(false));
  }, [source, jobId]);

  useEffect(() => {
    fetch(`/api/v1/jobs/${source}/${jobId}/package/files`)
      .then((r) => (r.ok ? r.json() : { files: [] }))
      .then((d) => setPackageFiles(d.files ?? []))
      .catch(() => setPackageFiles([]));
  }, [source, jobId]);

  const isComplete = timeline?.current_node === "package" || timeline?.current_node === "render";
  const requiredStages = ["scrape", "extract_understand", "match", "generate_documents"];
  const completedStages = requiredStages.filter((s) =>
    timeline?.stages.some((st) => st.stage === s && (st.status === "completed" || st.status === "paused_review"))
  );

  return (
    <section className="panel deployment-page">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to={`/jobs/${source}/${jobId}`}>{source} {jobId}</Link>
        <span>/</span>
        <span>Deployment</span>
      </div>

      <h1>Mission Status</h1>

      <div className={`mission-banner ${isComplete ? "mission-complete" : "mission-pending"}`}>
        <span className="material-symbols-outlined">
          {isComplete ? "task_alt" : "pending"}
        </span>
        <div>
          <strong>{isComplete ? "Bundle Ready" : "Bundle Pending"}</strong>
          <p>
            {completedStages.length}/{requiredStages.length} stages reviewed
          </p>
        </div>
      </div>

      <div className="checklist">
        <h2>Mission Checklist</h2>
        {requiredStages.map((stage) => {
          const stageInfo = timeline?.stages.find((s) => s.stage === stage);
          const done = stageInfo?.status === "completed" || stageInfo?.status === "paused_review";
          return (
            <div key={stage} className={`checklist-item ${done ? "checklist-done" : ""}`}>
              <span className="material-symbols-outlined">
                {done ? "check_circle" : "radio_button_unchecked"}
              </span>
              <span>{stage.replace(/_/g, " ")}</span>
              {stageInfo && (
                <span className={`status-chip status-${stageInfo.status.replace(/_/g, "_")}`}>
                  {stageInfo.status.replace(/_/g, " ")}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {packageFiles.length > 0 && (
        <div className="package-files">
          <h2>Bundle Contents</h2>
          {packageFiles.map((file) => (
            <div key={file.path} className="package-file-item">
              <span className="material-symbols-outlined">description</span>
              <div className="package-file-info">
                <strong>{file.name}</strong>
                <span>{file.size_kb.toFixed(1)} KB</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="submit-section">
        <button
          type="button"
          className="submit-btn"
          disabled={!isComplete}
          title={!isComplete ? "Complete all stage reviews before submitting" : "Ready to submit"}
        >
          <span className="material-symbols-outlined">send</span>
          Submit Application
        </button>
        {!isComplete && (
          <p className="submit-hint">Complete all stage reviews to enable submission</p>
        )}
        <p className="submit-note">
          Run <code>python -m src.cli.run_prep_match --resume</code> to continue pipeline
        </p>
      </div>
    </section>
  );
}
