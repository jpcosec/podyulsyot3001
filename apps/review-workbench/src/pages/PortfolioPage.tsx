import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getPortfolioSummary } from "../api/client";
import { JobTree } from "../components/JobTree";
import type { PortfolioSummary } from "../types/models";

const MAIN_WORKSTREAMS = [
  {
    title: "Node Editor",
    path: "/sandbox/node_editor",
    description: "Fullscreen graph editing with focus/filter/connect behavior.",
    area: "Current sandbox",
  },
  {
    title: "CV Graph Editor",
    path: "/sandbox/cv_graph",
    description: "Container-entry flows, skill linking, and layout behavior.",
    area: "Current sandbox",
  },
  {
    title: "Text Tagger",
    path: "/sandbox/text_tagger",
    description: "Text-to-node tagging and category interaction loop.",
    area: "Current sandbox",
  },
];

const DEV_BOOT_SEQUENCE = [
  "Run ./scripts/dev-all.sh to start UI + API + Neo4j",
  "Verify API is live at /health before UI checks",
  "Open /sandbox/node_editor for graph behavior iteration",
  "Open /sandbox/cv_graph for container + relation iteration",
  "Open /sandbox/text_tagger for text annotation flow checks",
  "Use job pages to verify timeline and review routing",
];

const OPERATOR_COMMANDS = [
  "python -m pytest tests/ -q",
  "python -m src.cli.run_prep_match --source tu_berlin --job-id 201588 --resume",
  "python -m src.cli.run_scrape_probe --source tu_berlin --mode listing --url https://www.jobs.tu-berlin.de/en/job-postings",
  "python -m src.cli.check_repo_protocol",
];

export function PortfolioPage(): JSX.Element {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    getPortfolioSummary().then(setSummary).catch((err: Error) => setError(err.message));
  }, []);

  const reviewQueue = (summary?.jobs ?? []).filter((job) => {
    const status = job.status.toLowerCase();
    return status.includes("review") || status.includes("paused") || job.current_node.includes("review");
  });
  reviewQueue.sort((left, right) => {
    const leftPaused = left.status === "paused_review" ? 1 : 0;
    const rightPaused = right.status === "paused_review" ? 1 : 0;
    if (leftPaused !== rightPaused) {
      return rightPaused - leftPaused;
    }
    return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
  });
  const nextReviewJob = reviewQueue[0] ?? null;
  const nextReviewResumeCommand = nextReviewJob
    ? `python -m src.cli.run_prep_match --source ${nextReviewJob.source} --job-id ${nextReviewJob.job_id} --resume`
    : "";

  return (
    <section className="panel">
      <h1>Application Portfolio</h1>
      <p>Development dashboard for sandbox exploration and runtime review operations.</p>

      <div className="review-queue-card">
        <h2>Review Queue</h2>
        {nextReviewJob ? (
          <>
            <p>
              Next likely review target: <strong>{nextReviewJob.source}</strong> job <strong>{nextReviewJob.job_id}</strong> at
              node <strong>{nextReviewJob.current_node}</strong>.{" "}
              <Link to={`/jobs/${nextReviewJob.source}/${nextReviewJob.job_id}`}>Open job workspace</Link>
            </p>
            <p className="review-next-step">
              Next action: edit decision markdown outside the UI, then resume with
              <code className="review-inline-code">{nextReviewResumeCommand}</code>
            </p>
          </>
        ) : (
          <p>No review-stage job detected yet. Use sandbox routes for UI iteration.</p>
        )}
      </div>

      <div className="review-queue-card">
        <h2>Data Explorer</h2>
        <p>
          <Link to="/explorer">Browse all local job artifacts</Link> — inspect JSON, Markdown, and screenshots in data/jobs/.
        </p>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {summary ? (
        <div className="stats-grid">
          <article>
            <h3>Total Jobs</h3>
            <strong>{summary.totals.jobs}</strong>
          </article>
          <article>
            <h3>Pending Review</h3>
            <strong>{summary.totals.pending_review}</strong>
          </article>
          <article>
            <h3>Completed</h3>
            <strong>{summary.totals.completed}</strong>
          </article>
          <article>
            <h3>Failed</h3>
            <strong>{summary.totals.failed}</strong>
          </article>
        </div>
      ) : (
        <p>Loading portfolio summary...</p>
      )}

      <h2>Jobs</h2>
      <JobTree jobs={summary?.jobs ?? []} />

      <details className="dev-section">
        <summary>Developer Tools</summary>
        <div className="dev-path-grid">
          <article className="dev-path-card">
            <h2>Current Workstream</h2>
            <p>Use these surfaces first while iterating graph/editor behavior.</p>
            <div className="workstream-links">
              {MAIN_WORKSTREAMS.map((flow) => (
                <Link key={flow.path} className="workstream-link" to={flow.path}>
                  <strong>{flow.title}</strong>
                  <span>{flow.description}</span>
                  <small>{flow.area}</small>
                </Link>
              ))}
            </div>
          </article>

          <article className="dev-path-card">
            <h2>Boot Sequence</h2>
            <ol className="boot-sequence-list">
              {DEV_BOOT_SEQUENCE.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <p>
              Need isolated previews? Open the <Link to="/sandbox">component sandbox</Link>.
            </p>
          </article>
        </div>

        <div className="review-queue-card">
          <h2>Operator Quick Commands</h2>
          <div className="operator-command-grid">
            {OPERATOR_COMMANDS.map((command) => (
              <code key={command} className="operator-command-chip">
                {command}
              </code>
            ))}
          </div>
        </div>
      </details>
    </section>
  );
}
