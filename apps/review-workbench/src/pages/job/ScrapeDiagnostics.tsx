import { useParams } from 'react-router-dom';
import { useArtifacts } from '../../features/job-pipeline/api/useArtifacts';
import { ScrapeMetaCard } from '../../features/job-pipeline/components/ScrapeMetaCard';
import { SourceTextPreview } from '../../features/job-pipeline/components/SourceTextPreview';
import { ErrorScreenshot } from '../../features/job-pipeline/components/ErrorScreenshot';
import { ScrapeControlPanel } from '../../features/job-pipeline/components/ScrapeControlPanel';
import { Spinner } from '../../components/atoms/Spinner';

export function ScrapeDiagnostics() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const { data, isLoading, isError } = useArtifacts(source!, jobId!, 'scrape');

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

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-auto p-6 space-y-4">
        <div>
          <p className="font-mono text-[10px] text-primary uppercase tracking-widest">Scrape</p>
          <h1 className="font-headline text-xl font-bold text-on-surface mt-1">Scrape Diagnostics</h1>
        </div>
        <ScrapeMetaCard files={data.files} />
        <SourceTextPreview files={data.files} />
        <ErrorScreenshot files={data.files} />
      </div>
      <ScrapeControlPanel
        source={source!}
        jobId={jobId!}
        hasData={data.files.length > 0}
      />
    </div>
  );
}
