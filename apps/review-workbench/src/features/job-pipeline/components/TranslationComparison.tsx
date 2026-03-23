import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '../../../utils/cn';

interface Props {
  originalText: string;
  translatedText: string;
  originalLanguage: string;
  targetLanguage: string;
}

const LANG_LABELS: Record<string, string> = {
  de: 'Deutsch',
  en: 'English',
  es: 'Español',
  fr: 'Français',
};

const markdownStyles = {
  h1: 'text-lg font-bold text-on-surface mb-2 mt-3 first:mt-0',
  h2: 'text-base font-semibold text-on-surface mb-2 mt-3 first:mt-0',
  h3: 'text-sm font-semibold text-on-surface mb-1 mt-2 first:mt-0',
  p: 'text-sm text-on-surface mb-2 leading-relaxed',
  ul: 'text-sm text-on-surface mb-2 pl-4 list-disc space-y-1',
  ol: 'text-sm text-on-surface mb-2 pl-4 list-decimal space-y-1',
  li: 'text-sm text-on-surface leading-relaxed',
  strong: 'font-semibold text-on-surface',
  a: 'text-primary hover:underline',
  blockquote: 'text-sm text-on-muted italic border-l-2 border-primary/30 pl-3 my-2',
  code: 'font-mono text-xs bg-surface-container px-1 py-0.5 rounded',
  pre: 'text-xs bg-surface-container p-3 rounded overflow-x-auto mb-2',
};

function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="[&>h1]:text-lg [&>h1]:font-bold [&>h1]:text-on-surface [&>h1]:mb-2 [&>h1]:mt-3 [&>h1:first-child]:mt-0 [&>h2]:text-base [&>h2]:font-semibold [&>h2]:text-on-surface [&>h2]:mb-2 [&>h2]:mt-3 [&>h2:first-child]:mt-0 [&>p]:text-sm [&>p]:text-on-surface [&>p]:mb-2 [&>p]:leading-relaxed [&>ul]:text-sm [&>ul]:text-on-surface [&>ul]:mb-2 [&>ul]:pl-4 [&>ul]:list-disc [&>ol]:text-sm [&>ol]:text-on-surface [&>ol]:mb-2 [&>ol]:pl-4 [&>li]:text-sm [&>li]:text-on-surface [&>li]:leading-relaxed [&>strong]:font-semibold [&>a]:text-primary [&>a:hover]:underline">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}

export function TranslationComparison({ originalText, translatedText, originalLanguage, targetLanguage }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-surface-container-low border border-outline/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">
          Translation Comparison
        </p>
        <button
          onClick={() => setExpanded(!expanded)}
          className="font-mono text-[10px] text-primary hover:text-primary-dim uppercase tracking-widest"
        >
          {expanded ? '[ COLLAPSE ]' : '[ EXPAND ]'}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="border border-outline/20 rounded overflow-hidden">
          <div className="px-4 py-3 bg-surface border-b border-outline/20">
            <span className="font-mono text-[10px] text-on-muted uppercase tracking-widest">
              Original ({LANG_LABELS[originalLanguage] ?? originalLanguage})
            </span>
          </div>
          <div className={cn(
            'bg-surface-low p-4 overflow-auto',
            !expanded && 'max-h-96'
          )}>
            <MarkdownContent content={originalText} />
          </div>
        </div>

        <div className="border border-outline/20 rounded overflow-hidden">
          <div className="px-4 py-3 bg-surface border-b border-outline/20">
            <span className="font-mono text-[10px] text-on-muted uppercase tracking-widest">
              Translated ({LANG_LABELS[targetLanguage] ?? targetLanguage})
            </span>
          </div>
          <div className={cn(
            'bg-surface-low p-4 overflow-auto',
            !expanded && 'max-h-96'
          )}>
            <MarkdownContent content={translatedText} />
          </div>
        </div>
      </div>
    </div>
  );
}
