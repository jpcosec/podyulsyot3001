import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/atoms/Button';

interface Props {
  source: string;
  jobId: string;
  hasData: boolean;
}

export function ScrapeControlPanel({ source, jobId, hasData }: Props) {
  const navigate = useNavigate();

  return (
    <div className="w-80 bg-background border-l border-secondary/20 p-4 flex flex-col gap-4">
      <div>
        <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em] mb-1">Phase</p>
        <p className="font-headline font-bold text-on-surface uppercase tracking-widest text-sm">Scrape</p>
      </div>

      <div className="border-t border-outline/20 pt-4 space-y-2 font-mono text-xs">
        <div className="flex justify-between">
          <span className="text-on-muted">SOURCE</span>
          <span className="text-on-surface uppercase">{source}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-on-muted">STATUS</span>
          <span className="text-primary">{hasData ? 'COMPLETED' : 'PENDING'}</span>
        </div>
      </div>

      <div className="border-t border-outline/20 pt-4 space-y-2 mt-auto">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-center"
          disabled
          title="Backend required"
        >
          RE-RUN SCRAPE
        </Button>
        <Button
          variant="primary"
          size="sm"
          className="w-full justify-center"
          onClick={() => navigate(`/jobs/${source}/${jobId}/extract`)}
        >
          ADVANCE →
        </Button>
      </div>
    </div>
  );
}
