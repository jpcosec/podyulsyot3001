import { useNavigate } from 'react-router-dom';
import { Badge } from '../../../components/atoms/Badge';
import { cn } from '../../../utils/cn';
import type { StageItem } from '../../../types/api.types';

interface Props {
  source: string;
  jobId: string;
  stage: StageItem;
}

const STAGE_ROUTE_MAP: Record<string, string> = {
  scrape: 'scrape',
  translate_if_needed: 'scrape',
  extract_understand: 'extract',
  match: 'match',
  review_match: 'match',
  generate_documents: 'sculpt',
  render: 'sculpt',
  package: 'deployment',
};

function getDotColor(status: string): string {
  switch (status) {
    case 'approved':
      return 'text-primary';
    case 'needs_review':
    case 'pending_hitl':
      return 'text-secondary animate-pulse';
    case 'running':
      return 'text-secondary';
    case 'error':
      return 'text-error';
    case 'pending':
      return 'text-on-muted';
    default:
      return 'text-on-muted';
  }
}

function getDotChar(status: string): string {
  if (status === 'pending') return '○';
  return '●';
}

function getStatusBadgeVariant(status: string): 'primary' | 'secondary' | 'danger' | 'muted' {
  switch (status) {
    case 'approved':
      return 'primary';
    case 'needs_review':
    case 'pending_hitl':
      return 'secondary';
    case 'error':
      return 'danger';
    default:
      return 'muted';
  }
}

export function StageRow({ source, jobId, stage }: Props) {
  const navigate = useNavigate();
  const routeSuffix = STAGE_ROUTE_MAP[stage.name] || stage.name;

  const handleStageClick = () => {
    navigate(`/jobs/${source}/${jobId}/${routeSuffix}`);
  };

  return (
    <div className="flex items-center gap-3">
      <span className={cn('text-lg font-bold', getDotColor(stage.status))}>
        {getDotChar(stage.status)}
      </span>
      <button
        onClick={handleStageClick}
        className="font-headline uppercase tracking-widest text-sm text-on-surface hover:text-primary transition-colors"
      >
        {stage.name}
      </button>
      <Badge variant={getStatusBadgeVariant(stage.status)}>
        {stage.status.replace(/_/g, ' ')}
      </Badge>
      {stage.artifact_ref && (
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            // TODO: navigate to Data Explorer with artifact path
          }}
          className="font-mono text-[10px] text-primary hover:underline ml-auto"
        >
          {stage.artifact_ref}
        </a>
      )}
    </div>
  );
}
