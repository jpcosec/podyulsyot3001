import { useNavigate } from 'react-router-dom';
import { ControlPanel } from '../../../components/molecules/ControlPanel';
import { cn } from '../../../utils/cn';

interface Props {
  source: string;
  jobId: string;
  hasData: boolean;
  url?: string;
  adapter?: string;
  httpStatus?: number;
  fetchedAt?: string;
}

export function ScrapeControlPanel({ source, jobId, hasData, url, adapter, httpStatus, fetchedAt }: Props) {
  const navigate = useNavigate();

  const httpColor = httpStatus
    ? httpStatus >= 200 && httpStatus < 300 ? 'text-primary' : 'text-error'
    : '';

  return (
    <ControlPanel
      title="Scrape"
      phaseColor="secondary"
      status={{ label: 'Status', value: hasData ? 'COMPLETED' : 'PENDING', variant: hasData ? 'primary' : 'muted' }}
      fields={[
        ...(adapter ? [{ label: 'Adapter', value: adapter.toUpperCase(), mono: true }] : []),
        ...(httpStatus ? [{ label: 'HTTP', value: <span className={cn('font-mono', httpColor)}>{httpStatus}</span> }] : []),
        ...(fetchedAt ? [{ label: 'Fetched', value: new Date(fetchedAt).toLocaleString() }] : []),
      ]}
      actions={[
        { label: 'RE-RUN SCRAPE', variant: 'ghost', disabled: true, onClick: () => {} },
        { label: 'ADVANCE →', variant: 'primary', onClick: () => navigate(`/jobs/${source}/${jobId}/translate`) },
      ]}
    >
      {url && (
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">URL</p>
          <p className="font-mono text-[9px] text-on-surface break-all leading-relaxed">{url}</p>
        </div>
      )}
    </ControlPanel>
  );
}
