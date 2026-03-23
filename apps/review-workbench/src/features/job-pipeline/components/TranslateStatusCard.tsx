import { Check, X } from 'lucide-react';
import { cn } from '../../../utils/cn';

interface Props {
  translated: boolean;
  originalLanguage: string;
  targetLanguage: string;
  chunksProcessed: number;
}

const LANG_NAMES: Record<string, string> = {
  de: 'German',
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  it: 'Italian',
  pt: 'Portuguese',
  nl: 'Dutch',
  pl: 'Polish',
  ru: 'Russian',
  zh: 'Chinese',
  ja: 'Japanese',
  ko: 'Korean',
};

export function TranslateStatusCard({ translated, originalLanguage, targetLanguage, chunksProcessed }: Props) {
  return (
    <div className="bg-surface-container-low border border-outline/20 p-4">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em] mb-3">
        Translation Status
      </p>

      <div className="flex items-center gap-3 mb-4">
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 border font-mono text-[10px] uppercase tracking-widest',
            translated
              ? 'bg-primary/10 text-primary border-primary/30'
              : 'bg-surface-low text-on-muted border-outline/30'
          )}
        >
          {translated ? <Check size={12} /> : <X size={12} />}
          {translated ? 'TRANSLATED' : 'NO_TRANSLATION_NEEDED'}
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">Original</span>
          <span className="font-mono text-xs text-on-surface uppercase">
            {LANG_NAMES[originalLanguage] ?? originalLanguage} ({originalLanguage})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">Target</span>
          <span className="font-mono text-xs text-on-surface uppercase">
            {LANG_NAMES[targetLanguage] ?? targetLanguage} ({targetLanguage})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">Chunks</span>
          <span className="font-mono text-xs text-on-surface">{chunksProcessed} processed</span>
        </div>
      </div>
    </div>
  );
}
