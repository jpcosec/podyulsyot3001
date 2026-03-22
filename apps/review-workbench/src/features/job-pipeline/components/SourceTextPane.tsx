import { useRef, useState, useMemo } from 'react';
import { cn } from '../../../utils/cn';
import { toOffset } from '../../../utils/text-offsets';
import type { RequirementItem, RequirementTextSpan } from '../../../types/api.types';

interface Segment {
  start: number;
  end: number;
  text: string;
  priority?: string;
}

interface SelectedRange {
  start: number;
  end: number;
}

interface Props {
  markdown: string;
  highlight: RequirementTextSpan | null;
  requirements?: RequirementItem[];
  onSpanSelect?: (range: { start: number; end: number; text: string }) => void;
}

function buildSegments(text: string, reqs: RequirementItem[]): Segment[] {
  // Collect all reqs with valid char spans
  const spans = reqs
    .filter(r => r.char_start != null && r.char_end != null)
    .map(r => ({ start: r.char_start!, end: r.char_end!, priority: r.priority }))
    .sort((a, b) => a.start - b.start);

  if (spans.length === 0) {
    return [{ start: 0, end: text.length, text }];
  }

  const segments: Segment[] = [];
  let cursor = 0;

  for (const span of spans) {
    if (cursor < span.start) {
      segments.push({ start: cursor, end: span.start, text: text.slice(cursor, span.start) });
    }
    segments.push({
      start: span.start,
      end: span.end,
      text: text.slice(span.start, span.end),
      priority: span.priority,
    });
    cursor = span.end;
  }

  if (cursor < text.length) {
    segments.push({ start: cursor, end: text.length, text: text.slice(cursor) });
  }

  return segments;
}

export function SourceTextPane({ markdown, highlight, requirements = [], onSpanSelect }: Props) {
  const editorRef = useRef<HTMLPreElement>(null);
  const [selectedRange, setSelectedRange] = useState<SelectedRange | null>(null);
  const lines = markdown.split('\n');

  const segments = useMemo(() => buildSegments(markdown, requirements), [markdown, requirements]);

  const captureSelection = () => {
    const root = editorRef.current;
    const selection = window.getSelection();
    if (!root || !selection || selection.rangeCount === 0) {
      setSelectedRange(null);
      return;
    }
    const range = selection.getRangeAt(0);
    if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) {
      setSelectedRange(null);
      return;
    }
    const start = toOffset(root, range.startContainer, range.startOffset);
    const end = toOffset(root, range.endContainer, range.endOffset);
    const realStart = Math.max(0, Math.min(start, end));
    const realEnd = Math.min(markdown.length, Math.max(start, end));
    if (realStart === realEnd) { setSelectedRange(null); return; }
    setSelectedRange({ start: realStart, end: realEnd });
    if (onSpanSelect) {
      onSpanSelect({ start: realStart, end: realEnd, text: markdown.slice(realStart, realEnd) });
    }
  };

  // Check if any char-level segments exist; if not, use line-level highlighting
  const hasCharSpans = requirements.some(r => r.char_start != null && r.char_end != null);

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-outline/20">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">Source Text</p>
      </div>
      <div className="flex-1 overflow-auto bg-surface-low p-0 relative">
        {hasCharSpans ? (
          // Char-level rendering with segments
          <pre
            ref={editorRef}
            onMouseUp={captureSelection}
            className="font-mono text-xs text-on-surface whitespace-pre-wrap p-3 leading-5 select-text"
          >
            {segments.map((seg, i) =>
              seg.priority ? (
                <mark
                  key={i}
                  className={cn(
                    seg.priority === 'must'
                      ? 'bg-secondary/15 border-x border-secondary/40'
                      : 'bg-outline/10 border-x border-outline/30',
                    'rounded-none'
                  )}
                >
                  {seg.text}
                </mark>
              ) : (
                <span key={i}>{seg.text}</span>
              )
            )}
          </pre>
        ) : (
          // Line-level rendering (original behavior)
          <pre
            ref={editorRef}
            onMouseUp={captureSelection}
            className="font-mono text-xs text-on-surface whitespace-pre-wrap p-3 leading-5 select-text"
          >
            {lines.map((line, i) => {
              const lineNum = i + 1;
              const isHighlighted =
                highlight !== null &&
                highlight.start_line !== null &&
                highlight.end_line !== null &&
                lineNum >= highlight.start_line &&
                lineNum <= highlight.end_line;

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
        )}

        {/* Floating hint when text is selected and onSpanSelect is provided */}
        {selectedRange && onSpanSelect && (
          <div className="fixed bottom-4 left-1/2 -translate-x-1/2 font-mono text-[10px] bg-surface-container border border-primary/30 px-3 py-1.5 z-50 pointer-events-none shadow-md">
            Press <kbd className="font-mono bg-surface border border-outline/30 px-1">1</kbd> = MUST &nbsp;·&nbsp;
            <kbd className="font-mono bg-surface border border-outline/30 px-1">2</kbd> = NICE &nbsp;·&nbsp;
            <kbd className="font-mono bg-surface border border-outline/30 px-1">Esc</kbd> = cancel
          </div>
        )}
      </div>
    </div>
  );
}
