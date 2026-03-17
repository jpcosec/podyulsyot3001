import { Link } from "react-router-dom";

import type { JobListItem } from "../types/models";

export function JobTree({ jobs }: { jobs: JobListItem[] }): JSX.Element {
  if (jobs.length === 0) {
    return <p>No jobs found in the current data root.</p>;
  }

  return (
    <nav className="job-tree">
      {jobs.map((job) => (
        <Link
          key={`${job.source}-${job.job_id}`}
          className="job-tree-item"
          to={`/jobs/${job.source}/${job.job_id}`}
        >
          <span>{job.source}</span>
          <strong>{job.job_id}</strong>
        </Link>
      ))}
    </nav>
  );
}
