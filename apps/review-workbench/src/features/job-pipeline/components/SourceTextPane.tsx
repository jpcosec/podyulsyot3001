import { cn } from '../../../utils/cn';
import type { RequirementTextSpan } from '../../../types/api.types';

interface Props {
  markdown: string;
  highlight: RequirementTextSpan | null;
}

export function SourceTextPane({ markdown, highlight }: Props) {
  const lines = markdown.split('\n');

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-outline/20">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">Source Text</p>
      </div>
      <div className="flex-1 overflow-auto bg-surface-low p-0">
        <pre className="font-mono text-xs text-on-surface whitespace-pre-wrap p-3 leading-5">
          {lines.map((line, i) => {
            const lineNum = i + 1;
            const isHighlighted =
              highlight?.start_line !== null &&
              highlight?.end_line !== null &&
              lineNum >= (highlight.start_line ?? 0) &&
              lineNum <= (highlight.end_line ?? 0);

            return (
              <div
                key={i}
                className={cn(
                  'flex gap-3 px-1',
                  isHighlighted && 'bg-primary/15 border-x border-primary/60 px-0.5'
                )}
              >
                <span className="text-on-muted select-none w-6 text-right flex-shrink-0 text-[9px] leading-5">
                  {lineNum}
                </span>
                <span>{line}</span>
              </div>
            );
          })}
        </pre>
      </div>
    </div>
  );
}
