import { useParams, Link } from 'react-router-dom';
import { useJobTimeline } from '../../features/job-pipeline/api/useJobTimeline';
import { HitlCtaBanner } from '../../features/job-pipeline/components/HitlCtaBanner';
import { PipelineTimeline } from '../../features/job-pipeline/components/PipelineTimeline';
import { JobMetaPanel } from '../../features/job-pipeline/components/JobMetaPanel';
import { Badge } from '../../components/atoms/Badge';

export function JobFlowInspector() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const { data, isLoading, isError } = useJobTimeline(source!, jobId!);

  if (isLoading) {
    return <div className="p-6 font-mono text-on-muted text-sm">Loading...</div>;
  }

  if (isError || !data) {
    return (
      <div className="p-6">
        <p className="font-mono text-xs text-on-muted uppercase tracking-widest mb-2">Timeline</p>
        <p className="font-mono text-error text-sm mb-3">Unable to load timeline</p>
        <Link to="/" className="font-mono text-[10px] text-primary hover:underline">
          ← PORTFOLIO
        </Link>
        <button
          onClick={() => window.location.reload()}
          className="ml-4 font-mono text-[10px] text-on-muted hover:text-on-surface underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <h1 className="font-headline font-bold text-lg text-on-surface uppercase">{data.job_id}</h1>
        <span className="font-mono text-on-muted text-sm">/ {data.source}</span>
        <Badge variant="muted">{data.status.replace(/_/g, ' ')}</Badge>
      </div>

      {data.status === 'pending_hitl' && (
        <HitlCtaBanner source={source!} jobId={jobId!} currentNode={data.current_node} />
      )}

      <PipelineTimeline source={source!} jobId={jobId!} stages={data.stages} />
      <JobMetaPanel timeline={data} />
    </div>
  );
}
