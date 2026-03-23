import { useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import { useArtifacts } from '../../features/job-pipeline/api/useArtifacts';
import { DiagnosticCard } from '../../components/molecules/DiagnosticCard';
import { ControlPanel } from '../../components/molecules/ControlPanel';
import { TranslationComparison } from '../../features/job-pipeline/components/TranslationComparison';
import { Spinner } from '../../components/atoms/Spinner';
import { Check, X } from 'lucide-react';

const LANG_NAMES: Record<string, string> = {
  de: 'German',
  en: 'English',
  es: 'Spanish',
  fr: 'French',
};

export function TranslateDiagnostics() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const { data, isLoading, isError } = useArtifacts(source!, jobId!, 'translate_if_needed');
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
        <p className="font-mono text-error text-sm">TRANSLATE_DATA_NOT_FOUND</p>
      </div>
    );
  }

  const stateFile = data.files.find(f => f.path.includes('state.json'));
  const state = stateFile ? JSON.parse(stateFile.content) : null;
  const originalFile = data.files.find(f => f.path.includes('source_original'));
  const translatedFile = data.files.find(f => f.path.includes('source_translated'));

  const translated = state?.translated ?? false;

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-auto p-6 space-y-4">
        <div>
          <p className="font-mono text-[10px] text-primary uppercase tracking-widest">Translate</p>
          <h1 className="font-headline text-xl font-bold text-on-surface mt-1">Translate Diagnostics</h1>
        </div>

        <DiagnosticCard title="Translation Status">
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-1.5 border font-mono text-[10px] uppercase tracking-widest ${
              translated
                ? 'bg-primary/10 text-primary border-primary/30'
                : 'bg-surface-low text-on-muted border-outline/30'
            }`}>
              {translated ? <Check size={12} /> : <X size={12} />}
              {translated ? 'TRANSLATED' : 'NO_TRANSLATION_NEEDED'}
            </div>
          </div>
        </DiagnosticCard>

        {translated && originalFile && translatedFile && (
          <TranslationComparison
            originalText={originalFile.content}
            translatedText={translatedFile.content}
            originalLanguage={state.original_language}
            targetLanguage={state.target_language}
          />
        )}
      </div>

      <ControlPanel
        title="Translate"
        phaseColor="secondary"
        status={{
          label: 'Status',
          value: translated ? 'TRANSLATED' : 'SKIPPED',
          variant: translated ? 'primary' : 'muted',
        }}
        fields={[
          { label: 'Languages', value: `${LANG_NAMES[state?.original_language] ?? state?.original_language} → ${LANG_NAMES[state?.target_language] ?? state?.target_language}` },
          ...(state?.chunks_processed ? [{ label: 'Chunks', value: `${state.chunks_processed} processed`, mono: true }] : []),
        ]}
        actions={[
          {
            label: 'ADVANCE →',
            variant: 'primary',
            onClick: () => navigate(`/jobs/${source}/${jobId}/extract`),
          },
        ]}
      />
    </div>
  );
}
