import { useNavigate } from 'react-router-dom';
import { ArrowRight, Check } from 'lucide-react';

interface Props {
  source: string;
  jobId: string;
  translated: boolean;
  originalLanguage?: string;
  targetLanguage?: string;
  chunksProcessed?: number;
}

const LANG_NAMES: Record<string, string> = {
  de: 'German',
  en: 'English',
  es: 'Spanish',
  fr: 'French',
};

export function TranslateControlPanel({ source, jobId, translated, originalLanguage, targetLanguage, chunksProcessed }: Props) {
  const navigate = useNavigate();

  return (
    <div className="w-72 border-l border-outline/20 bg-surface-container-low p-4 flex flex-col">
      <p className="font-mono text-[10px] text-secondary uppercase tracking-widest mb-4">
        Phase
      </p>
      <p className="font-headline text-lg text-secondary mb-6">Translate</p>

      <div className="space-y-4 text-xs">
        <div className="space-y-3">
          <div>
            <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">Status</p>
            <div className="flex items-center gap-2">
              <Check size={14} className="text-primary" />
              <span className="text-primary uppercase font-mono text-[10px]">
                {translated ? 'TRANSLATED' : 'SKIPPED'}
              </span>
            </div>
          </div>

          {translated && (
            <>
              <div>
                <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">Languages</p>
                <p className="text-on-surface">
                  {LANG_NAMES[originalLanguage ?? ''] ?? originalLanguage} → {LANG_NAMES[targetLanguage ?? ''] ?? targetLanguage}
                </p>
              </div>

              {chunksProcessed && (
                <div>
                  <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">Chunks</p>
                  <p className="text-on-surface">{chunksProcessed} processed</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <div className="mt-auto pt-6 space-y-2">
        <button
          onClick={() => navigate(`/jobs/${source}/${jobId}/extract`)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary/10 border border-primary/30 text-primary font-mono text-[10px] uppercase tracking-widest hover:bg-primary/20 transition-colors"
        >
          Advance
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
