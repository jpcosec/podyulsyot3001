import { useNavigate } from 'react-router-dom';
import type { JobStatus, PortfolioSummary } from '../../../types/api.types';
import { Badge } from '../../../components/atoms/Badge';

const STATUS_VARIANT: Record<JobStatus, 'primary' | 'secondary' | 'success' | 'danger' | 'muted'> = {
  completed:    'success',
  pending_hitl: 'secondary',
  running:      'primary',
  failed:       'danger',
  archived:     'muted',
};

interface Props {
  data?: PortfolioSummary;
  loading: boolean;
  error: boolean;
}

export function PortfolioTable({ data, loading, error }: Props) {
  const navigate = useNavigate();

  if (loading) return <p className="text-on-muted font-mono text-sm">Loading...</p>;
  if (error)   return <p className="text-error font-mono text-sm">Failed to load portfolio.</p>;
  if (!data)   return null;

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="text-[10px] font-mono text-on-muted uppercase tracking-widest border-b border-outline/20">
          <th className="text-left py-2 pr-6">Source / Job ID</th>
          <th className="text-left py-2 pr-6">Current Stage</th>
          <th className="text-left py-2 pr-6">Status</th>
          <th className="text-left py-2">Updated</th>
        </tr>
      </thead>
      <tbody>
        {data.jobs.map((job) => (
          <tr
            key={job.job_id}
            className="border-b border-outline/10 hover:bg-surface-low transition-colors cursor-pointer"
            onClick={() => navigate(`/jobs/${job.source}/${job.job_id}`)}
          >
            <td className="py-3 pr-6 font-mono">
              <span className="text-on-muted">{job.source} / </span>
              <span className="text-primary">{job.job_id}</span>
            </td>
            <td className="py-3 pr-6 font-mono text-on-surface">{job.current_node}</td>
            <td className="py-3 pr-6">
              <Badge variant={STATUS_VARIANT[job.status] ?? 'muted'}>{job.status}</Badge>
            </td>
            <td className="py-3 font-mono text-on-muted text-xs">{job.updated_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
