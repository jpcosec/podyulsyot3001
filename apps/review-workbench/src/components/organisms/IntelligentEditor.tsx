import { useCallback, useMemo } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { json } from '@codemirror/lang-json';
import { oneDark } from '@codemirror/theme-one-dark';
import { EditorView, Decoration, type DecorationSet } from '@codemirror/view';
import { StateField } from '@codemirror/state';
import { RangeSetBuilder } from '@codemirror/state';
import { cn } from '../../utils/cn';
import type { RequirementItem } from '../../types/api.types';

type EditorMode = 'fold' | 'tag-hover' | 'diff';
type EditorLanguage = 'markdown' | 'json' | 'text';

interface Highlight {
  from: number;
  to: number;
  className?: string;
  priority?: 'must' | 'nice';
}

interface Props {
  mode: EditorMode;
  content: string;
  language?: EditorLanguage;
  highlights?: Highlight[];
  requirements?: RequirementItem[];
  readOnly?: boolean;
  onChange?: (value: string) => void;
  onSpanSelect?: (range: { start: number; end: number; text: string }) => void;
  className?: string;
}

const terranTheme = EditorView.theme({
  '&': { backgroundColor: 'transparent', fontSize: '12px' },
  '.cm-content': { fontFamily: 'JetBrains Mono, monospace', padding: '12px 0' },
  '.cm-gutters': {
    backgroundColor: 'transparent',
    borderRight: '1px solid rgba(132, 148, 149, 0.1)',
    color: '#849495',
    fontSize: '10px',
  },
  '.cm-lineNumbers .cm-gutterElement': { padding: '0 8px 0 12px', minWidth: '32px' },
  '.cm-activeLine': { backgroundColor: 'rgba(0, 242, 255, 0.05)' },
  '.cm-selectionBackground, ::selection': { backgroundColor: 'rgba(0, 242, 255, 0.2) !important' },
  '.cm-cursor': { borderLeftColor: '#00f2ff' },
});

const highlightStyles = EditorView.baseTheme({
  '.cm-highlight-must': {
    backgroundColor: 'rgba(255, 170, 0, 0.15)',
    borderLeft: '2px solid rgba(255, 170, 0, 0.5)',
    borderRight: '2px solid rgba(255, 170, 0, 0.5)',
  },
  '.cm-highlight-nice': {
    backgroundColor: 'rgba(132, 148, 149, 0.1)',
    borderLeft: '2px solid rgba(132, 148, 149, 0.3)',
    borderRight: '2px solid rgba(132, 148, 149, 0.3)',
  },
});

function buildDecorationField(highlights: Highlight[]) {
  return StateField.define<DecorationSet>({
    create(state) {
      if (highlights.length === 0) return Decoration.none;
      const builder = new RangeSetBuilder<Decoration>();
      const docLength = state.doc.length;
      const sorted = [...highlights].sort((a, b) => a.from - b.from);
      for (const h of sorted) {
        if (h.from < h.to && h.className && h.to <= docLength) {
          builder.add(h.from, h.to, Decoration.mark({ class: h.className }));
        }
      }
      return builder.finish();
    },
    update(deco) { return deco; },
    provide: f => EditorView.decorations.from(f),
  });
}

export function IntelligentEditor({
  mode,
  content,
  language = 'markdown',
  highlights = [],
  requirements = [],
  readOnly = false,
  onChange,
  onSpanSelect,
  className,
}: Props) {
  const allHighlights = useMemo(() => {
    if (mode !== 'tag-hover' || requirements.length === 0) return highlights;
    const reqHighlights = requirements
      .filter(r => r.char_start != null && r.char_end != null)
      .map(r => ({
        from: r.char_start!,
        to: r.char_end!,
        className: r.priority === 'must' ? 'cm-highlight-must' : 'cm-highlight-nice',
        priority: r.priority as 'must' | 'nice',
      }));
    return [...highlights, ...reqHighlights];
  }, [mode, highlights, requirements]);

  const extensions = useMemo(() => {
    const exts: Parameters<typeof CodeMirror>[0]['extensions'] = [
      terranTheme,
      highlightStyles,
      EditorView.lineWrapping,
    ];

    if (language === 'markdown') exts.push(markdown());
    else if (language === 'json') exts.push(json());

    if (mode === 'tag-hover' && allHighlights.length > 0) {
      exts.push(buildDecorationField(allHighlights));
    }

    if (onSpanSelect) {
      exts.push(
        EditorView.domEventHandlers({
          mouseup(_event, view) {
            const sel = view.state.selection.main;
            if (sel.empty) return;
            const text = view.state.sliceDoc(sel.from, sel.to);
            if (text.trim()) {
              onSpanSelect({ start: sel.from, end: sel.to, text });
            }
          },
        }),
      );
    }

    return exts;
  }, [mode, language, allHighlights, onSpanSelect]);

  const handleChange = useCallback((value: string) => {
    onChange?.(value);
  }, [onChange]);

  return (
    <div className={cn('h-full overflow-hidden', className)}>
      <CodeMirror
        value={content}
        height="100%"
        theme={oneDark}
        extensions={extensions}
        onChange={handleChange}
        editable={!readOnly}
        basicSetup={{
          lineNumbers: true,
          highlightActiveLineGutter: true,
          foldGutter: mode === 'fold',
          drawSelection: true,
          syntaxHighlighting: true,
          highlightActiveLine: true,
        }}
      />
    </div>
  );
}
