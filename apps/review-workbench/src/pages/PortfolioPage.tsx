import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getPortfolioSummary } from "../api/client";
import { JobTree } from "../components/JobTree";
import type { PortfolioSummary } from "../types/models";

export function PortfolioPage(): JSX.Element {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    getPortfolioSummary().then(setSummary).catch((err: Error) => setError(err.message));
  }, []);

  return (
    <section className="panel">
      <h1>Application Portfolio</h1>
      <p>UI-first review queue backed by filesystem read models.</p>
      <p>
        Need isolated UI testing? Open the <Link to="/sandbox">component sandbox</Link>.
      </p>
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
    </section>
  );
}
