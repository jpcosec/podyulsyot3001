import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getJobTimeline } from "../api/client";
import type { JobTimeline } from "../types/models";

interface ChecklistItem {
  label: string;
  checked: boolean;
}

function ChecklistItemComponent({ label, checked }: { label: string; checked: boolean }): JSX.Element {
  return (
    <li style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 0" }}>
      <span style={{ color: checked ? "var(--good)" : "var(--bad)", fontSize: "16px" }}>
        {checked ? "\u2713" : "\u2717"}
      </span>
      <span style={{ color: checked ? "var(--text-main)" : "var(--text-dim)" }}>{label}</span>
    </li>
  );
}

export function DeploymentPage(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [timeline, setTimeline] = useState<JobTimeline | null>(null);
  const [timelineError, setTimelineError] = useState("");
  const [bundleReady, setBundleReady] = useState<boolean | null>(null);

  useEffect(() => {
    getJobTimeline(source, jobId)
      .then((data) => {
        setTimeline(data);
        const hasPackage = data.artifacts && Object.keys(data.artifacts).some((k) => k.includes("package"));
        setBundleReady(hasPackage ?? false);
      })
      .catch((err: Error) => setTimelineError(err.message));
  }, [source, jobId]);

  const checklistItems: ChecklistItem[] = [
    { label: "All stages reviewed and approved", checked: timeline?.status === "completed" },
    {
      label: "Motivation letter reviewed",
      checked: timeline?.stages
        ? timeline.stages.some((s) => s.stage === "review_motivation_letter" && s.status === "completed")
        : false,
    },
    {
      label: "CV reviewed",
      checked: timeline?.stages
        ? timeline.stages.some((s) => s.stage === "review_cv" && s.status === "completed")
        : false,
    },
    {
      label: "Application email reviewed",
      checked: timeline?.stages
        ? timeline.stages.some((s) => s.stage === "review_email" && s.status === "completed")
        : false,
    },
  ];

  const allChecked = checklistItems.every((item) => item.checked);

  return (
    <section className="panel">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to={`/jobs/${source}/${jobId}`}>
          {source} {jobId}
        </Link>
        <span>/</span>
        <span>Deployment</span>
      </div>

      <h1>Deployment</h1>
      <p>Final stage: package and submit application artifacts.</p>

      {timelineError ? (
        <p className="error">{timelineError}</p>
      ) : !timeline ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="panel" style={{ marginTop: "16px" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "12px" }}>Mission Status</h2>
            <p style={{ margin: "0 0 12px" }}>
              Current status: <strong>{timeline.status}</strong>
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {checklistItems.map((item, idx) => (
                <ChecklistItemComponent key={idx} label={item.label} checked={item.checked} />
              ))}
            </ul>
          </div>

          <div className="panel" style={{ marginTop: "16px" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "12px" }}>Bundle Status</h2>
            {bundleReady === null ? (
              <p>Checking bundle...</p>
            ) : bundleReady ? (
              <p style={{ color: "var(--good)" }}>
                <strong>Ready</strong> - Package artifacts found
              </p>
            ) : (
              <p style={{ color: "var(--warn)" }}>
                <strong>Pending</strong> - Run pipeline to generate package
              </p>
            )}
            {timeline.artifacts && Object.keys(timeline.artifacts).length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <h4 style={{ margin: "0 0 8px", fontSize: "0.9rem", color: "var(--text-dim)" }}>
                  Available Artifacts
                </h4>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {Object.entries(timeline.artifacts).map(([key, ref]) => (
                    <li
                      key={key}
                      style={{
                        padding: "4px 0",
                        fontSize: "13px",
                        color: "var(--text-dim)",
                      }}
                    >
                      {key}: <code style={{ fontSize: "12px" }}>{ref}</code>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="panel" style={{ marginTop: "16px" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "12px" }}>Version & History</h2>
            <p style={{ margin: "0 0 8px", fontSize: "13px" }}>
              Job ID: <strong>{jobId}</strong>
            </p>
            <p style={{ margin: "0 0 8px", fontSize: "13px" }}>
              Source: <strong>{source}</strong>
            </p>
            <p style={{ margin: "0 0 8px", fontSize: "13px" }}>
              Thread: <code style={{ fontSize: "12px" }}>{timeline.thread_id}</code>
            </p>
            <p style={{ margin: "0 0 8px", fontSize: "13px" }}>
              Last updated: <strong>{new Date(timeline.updated_at).toLocaleString()}</strong>
            </p>
            <p style={{ margin: 0, fontSize: "13px" }}>
              Current node: <strong>{timeline.current_node}</strong>
            </p>
          </div>

          <div style={{ marginTop: "20px", display: "flex", gap: "12px", alignItems: "center" }}>
            <button
              type="button"
              disabled={!allChecked}
              title={allChecked ? "Ready to submit" : "Complete all checklist items first"}
              style={{
                padding: "10px 24px",
                borderRadius: "8px",
                border: "1px solid var(--line)",
                background: allChecked ? "var(--good)" : "var(--pending)",
                color: "#fff",
                fontSize: "14px",
                fontWeight: 600,
                cursor: allChecked ? "pointer" : "not-allowed",
                opacity: allChecked ? 1 : 0.6,
              }}
            >
              Submit Application
            </button>
            {!allChecked && (
              <span style={{ fontSize: "12px", color: "var(--text-dim)" }}>
                Complete all checklist items to enable submission
              </span>
            )}
            <span
              style={{
                marginLeft: "auto",
                fontSize: "12px",
                color: "var(--text-dim)",
                fontStyle: "italic",
              }}
            >
              Not implemented - run{" "}
              <code
                style={{
                  background: "#f1f5f9",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  fontSize: "11px",
                }}
              >
                python -m src.cli.run_prep_match --resume
              </code>
            </span>
          </div>
        </>
      )}
    </section>
  );
}
