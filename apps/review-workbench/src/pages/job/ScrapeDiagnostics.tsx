import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import { useArtifacts } from '../../features/job-pipeline/api/useArtifacts';
import { DiagnosticCard } from '../../components/molecules/DiagnosticCard';
import { ControlPanel } from '../../components/molecules/ControlPanel';
import { SourceTextPreview } from '../../features/job-pipeline/components/SourceTextPreview';
import { ErrorScreenshot } from '../../features/job-pipeline/components/ErrorScreenshot';
import { Spinner } from '../../components/atoms/Spinner';
import { cn } from '../../utils/cn';

export function ScrapeDiagnostics() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const { data, isLoading, isError } = useArtifacts(source!, jobId!, 'scrape');
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="md" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-6">
        <p className="font-mono text-error text-sm">SCRAPE_DATA_NOT_FOUND</p>
      </div>
    );
  }

  const metaFile = data.files.find(f => f.path.endsWith('fetch_metadata.json'));
  let meta: Record<string, unknown> = {};
  try {
    if (metaFile?.content) meta = JSON.parse(metaFile.content);
  } catch { /* ignore */ }

  const hasData = data.files.length > 0;
  const httpStatus = meta.http_status as number;

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-auto p-6 space-y-4">
        <div>
          <p className="font-mono text-[10px] text-primary uppercase tracking-widest">Scrape</p>
          <h1 className="font-headline text-xl font-bold text-on-surface mt-1">Scrape Diagnostics</h1>
        </div>

        <DiagnosticCard title="Fetch Metadata">
          <div className="space-y-3 text-sm">
            <div>
              <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">URL</p>
              <p className="font-mono text-xs text-on-surface break-all">{(meta.url as string) ?? '—'}</p>
            </div>
            <div className="flex gap-6">
              <div>
                <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">Adapter</p>
                <p className="font-mono text-xs text-on-surface uppercase">{((meta.adapter as string) ?? '—')}</p>
              </div>
              <div>
                <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">HTTP</p>
                <p className={cn(
                  'font-mono text-xs',
                  httpStatus >= 200 && httpStatus < 300 ? 'text-primary' : 'text-error'
                )}>
                  {httpStatus ?? '—'}
                </p>
              </div>
            </div>
            {(meta.fetched_at as string) && (
              <div>
                <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">Timestamp</p>
                <p className="font-mono text-xs text-on-surface">{new Date(meta.fetched_at as string).toLocaleString()}</p>
              </div>
            )}
          </div>
        </DiagnosticCard>

        <SourceTextPreview files={data.files} />
        <ErrorScreenshot files={data.files} />
      </div>

      <ControlPanel
        title="Scrape"
        phaseColor="secondary"
        status={{
          label: 'Status',
          value: hasData ? 'COMPLETED' : 'PENDING',
          variant: hasData ? 'primary' : 'muted',
        }}
        fields={[
          { label: 'Adapter', value: ((meta.adapter as string) ?? '—').toUpperCase(), mono: true },
          { label: 'HTTP', value: httpStatus ?? '—', mono: true },
        ]}
        actions={[
          {
            label: 'RE-RUN SCRAPE',
            variant: 'ghost',
            disabled: true,
            onClick: () => {},
          },
          {
            label: 'ADVANCE →',
            variant: 'primary',
            onClick: () => navigate(`/jobs/${source}/${jobId}/translate`),
          },
        ]}
      />
    </div>
  );
}
