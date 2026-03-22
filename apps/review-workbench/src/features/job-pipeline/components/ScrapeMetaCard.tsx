import type { ArtifactFile } from '../../../types/api.types';
import { cn } from '../../../utils/cn';

interface Props {
  files: ArtifactFile[];
}

export function ScrapeMetaCard({ files }: Props) {
  const metaFile = files.find(f => f.path.endsWith('fetch_metadata.json'));
  let meta: Record<string, unknown> = {};
  try {
    if (metaFile?.content) meta = JSON.parse(metaFile.content);
  } catch { /* ignore */ }

  const url = (meta.url as string) ?? '—';
  const fetched = (meta.fetched_at as string) ?? '—';
  const adapter = (meta.adapter as string) ?? '—';
  const httpStatus = (meta.http_status as number) ?? null;

  return (
    <div className="bg-surface-container-low border border-outline/20 p-4">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em] mb-3">Fetch Metadata</p>
      <div className="space-y-2">
        <div className="flex gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">URL</span>
          <span className="font-mono text-xs text-on-surface truncate">{url}</span>
        </div>
        <div className="flex gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">FETCHED</span>
          <span className="font-mono text-xs text-on-surface">{fetched}</span>
        </div>
        <div className="flex gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">ADAPTER</span>
          <span className="font-mono text-xs text-on-surface uppercase">{adapter}</span>
        </div>
        {httpStatus !== null && (
          <div className="flex gap-2">
            <span className="font-mono text-[10px] text-on-muted w-24">HTTP</span>
            <span className={cn(
              'font-mono text-xs',
              httpStatus >= 200 && httpStatus < 300 ? 'text-primary' : 'text-error'
            )}>
              {httpStatus}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
