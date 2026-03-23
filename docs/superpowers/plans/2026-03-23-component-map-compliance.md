# Component Map Compliance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor all remaining pages to use the organisms/molecules from `component_map.md`, then validate with TestSprite E2E.

**Architecture:** Feature components become thin wrappers over generic organisms (IntelligentEditor, GraphCanvas, FileTree, ControlPanel). Pages stay dumb — no logic changes, only swap internal rendering to organisms.

**Tech Stack:** React 18, TypeScript, @uiw/react-codemirror, @xyflow/react, dagre, Tailwind CSS, TestSprite

---

## Files

### Create / Modify

| File | Action | Why |
|------|--------|-----|
| `src/components/organisms/IntelligentEditor.tsx` | Modify | Fix broken decoration (async in sync context), add `onSpanSelect` prop |
| `src/features/job-pipeline/components/SourceTextPane.tsx` | Modify | Use IntelligentEditor internally |
| `src/features/job-pipeline/components/DocumentEditor.tsx` | Modify | Use IntelligentEditor internally |
| `src/features/job-pipeline/components/ScrapeControlPanel.tsx` | Modify | Use ControlPanel molecule |
| `src/features/job-pipeline/components/ExtractControlPanel.tsx` | Modify | Use ControlPanel molecule |
| `src/features/job-pipeline/components/MatchControlPanel.tsx` | Modify | Use ControlPanel molecule + children for detail |
| `src/components/organisms/GraphCanvas.tsx` | Modify | Add `onConnect` prop for manual edge creation |
| `src/features/job-pipeline/components/MatchGraphCanvas.tsx` | Modify | Use GraphCanvas internally |
| `src/features/explorer/components/ExplorerTree.tsx` | Modify | Delegate to FileTree organism |
| `src/features/explorer/components/JsonPreview.tsx` | Modify | Use IntelligentEditor (fold, json) |
| `src/features/explorer/components/MarkdownPreview.tsx` | Modify | Use IntelligentEditor (fold, markdown) |
| `src/features/base-cv/components/CvGraphCanvas.tsx` | Modify | Use GraphCanvas (layout=manual, custom nodeTypes) |

---

## Task 1: Fix IntelligentEditor — decorations + onSpanSelect

**Files:**
- Modify: `src/components/organisms/IntelligentEditor.tsx`

The current `tag-hover` mode has broken decoration code: `EditorView.decorations.compute` with an async `import()` inside — this returns a Promise, not a DecorationSet.

Fix with a `StateField` that holds the DecorationSet synchronously. Also add `onSpanSelect` prop for B2 tagging workflow.

- [ ] **Step 1: Replace IntelligentEditor with fixed version**

Replace the entire file with:

```tsx
import { useCallback, useMemo } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { json } from '@codemirror/lang-json';
import { oneDark } from '@codemirror/theme-one-dark';
import { EditorView, Decoration, DecorationSet } from '@codemirror/view';
import { StateField, StateEffect } from '@codemirror/state';
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
    create() {
      if (highlights.length === 0) return Decoration.none;
      const builder = new RangeSetBuilder<Decoration>();
      const sorted = [...highlights].sort((a, b) => a.from - b.from);
      for (const h of sorted) {
        if (h.from < h.to && h.className) {
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
  const reqHighlights = useMemo(() => {
    if (mode !== 'tag-hover' || requirements.length === 0) return highlights;
    const from_reqs = requirements
      .filter(r => r.char_start != null && r.char_end != null)
      .map(r => ({
        from: r.char_start!,
        to: r.char_end!,
        className: r.priority === 'must' ? 'cm-highlight-must' : 'cm-highlight-nice',
        priority: r.priority as 'must' | 'nice',
      }));
    return [...highlights, ...from_reqs];
  }, [mode, highlights, requirements]);

  const extensions = useMemo(() => {
    const exts: Parameters<typeof CodeMirror>[0]['extensions'] = [
      terranTheme,
      highlightStyles,
      EditorView.lineWrapping,
    ];
    if (language === 'markdown') exts.push(markdown());
    else if (language === 'json') exts.push(json());

    if (mode === 'fold') {
      // fold mode: no extra extensions
    } else if (mode === 'tag-hover' && reqHighlights.length > 0) {
      exts.push(buildDecorationField(reqHighlights));
    }

    if (onSpanSelect) {
      exts.push(
        EditorView.domEventHandlers({
          mouseup(event, view) {
            const sel = view.state.selection.main;
            if (sel.empty) return;
            const text = view.state.sliceDoc(sel.from, sel.to);
            if (text.trim()) {
              onSpanSelect({ start: sel.from, end: sel.to, text });
            }
          },
        })
      );
    }

    return exts;
  }, [mode, language, reqHighlights, onSpanSelect]);

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
```

- [ ] **Step 2: Verify build passes**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors related to IntelligentEditor.

- [ ] **Step 3: Commit**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign
git add apps/review-workbench/src/components/organisms/IntelligentEditor.tsx
git commit -m "fix(ui): fix IntelligentEditor decoration + add onSpanSelect (component_map)"
```

---

## Task 2: Refactor SourceTextPane to use IntelligentEditor

**Files:**
- Modify: `src/features/job-pipeline/components/SourceTextPane.tsx`

SourceTextPane has custom DOM-based text selection + segment rendering. Replace with IntelligentEditor (tag-hover mode) that now supports `onSpanSelect`.

- [ ] **Step 1: Replace SourceTextPane**

```tsx
import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';
import type { RequirementItem, RequirementTextSpan } from '../../../types/api.types';

interface Props {
  markdown: string;
  highlight: RequirementTextSpan | null;
  requirements?: RequirementItem[];
  onSpanSelect?: (range: { start: number; end: number; text: string }) => void;
}

export function SourceTextPane({ markdown, highlight, requirements = [], onSpanSelect }: Props) {
  // Build highlight from active highlight prop (line-based fallback if no char spans)
  const highlights = highlight?.char_start != null && highlight?.char_end != null
    ? [{ from: highlight.char_start, to: highlight.char_end, className: 'cm-highlight-must' }]
    : [];

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-outline/20">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">Source Text</p>
      </div>
      <div className="flex-1 overflow-hidden">
        <IntelligentEditor
          mode="tag-hover"
          content={markdown}
          language="markdown"
          highlights={highlights}
          requirements={requirements}
          readOnly={true}
          onSpanSelect={onSpanSelect}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build passes**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/components/SourceTextPane.tsx
git commit -m "refactor(ui): SourceTextPane uses IntelligentEditor (B2 tag-hover)"
```

---

## Task 3: Refactor DocumentEditor to use IntelligentEditor

**Files:**
- Modify: `src/features/job-pipeline/components/DocumentEditor.tsx`

DocumentEditor is just CodeMirror with markdown. Replace with IntelligentEditor (fold mode = editable markdown with syntax highlighting).

- [ ] **Step 1: Replace DocumentEditor**

```tsx
import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';

interface Props {
  content: string;
  onChange: (value: string) => void;
}

export function DocumentEditor({ content, onChange }: Props) {
  return (
    <IntelligentEditor
      mode="fold"
      content={content}
      language="markdown"
      onChange={onChange}
      className="h-full"
    />
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/components/DocumentEditor.tsx
git commit -m "refactor(ui): DocumentEditor uses IntelligentEditor (B4 fold mode)"
```

---

## Task 4: Refactor ScrapeControlPanel to use ControlPanel molecule

**Files:**
- Modify: `src/features/job-pipeline/components/ScrapeControlPanel.tsx`

ScrapeControlPanel has inline status/fields UI. Replace with generic ControlPanel, passing the URL as children since it's too long for the standard fields list.

- [ ] **Step 1: Replace ScrapeControlPanel**

```tsx
import { useNavigate } from 'react-router-dom';
import { ControlPanel } from '../../../components/molecules/ControlPanel';
import { cn } from '../../../utils/cn';

interface Props {
  source: string;
  jobId: string;
  hasData: boolean;
  url?: string;
  adapter?: string;
  httpStatus?: number;
  fetchedAt?: string;
}

export function ScrapeControlPanel({ source, jobId, hasData, url, adapter, httpStatus, fetchedAt }: Props) {
  const navigate = useNavigate();

  const httpColor = httpStatus
    ? (httpStatus >= 200 && httpStatus < 300 ? 'text-primary' : 'text-error')
    : '';

  return (
    <ControlPanel
      title="Scrape"
      phaseColor="secondary"
      status={{ label: 'Status', value: hasData ? 'COMPLETED' : 'PENDING', variant: hasData ? 'primary' : 'muted' }}
      fields={[
        ...(adapter ? [{ label: 'Adapter', value: adapter.toUpperCase(), mono: true }] : []),
        ...(httpStatus ? [{ label: 'HTTP', value: <span className={cn('font-mono', httpColor)}>{httpStatus}</span> }] : []),
        ...(fetchedAt ? [{ label: 'Fetched', value: new Date(fetchedAt).toLocaleString() }] : []),
      ]}
      actions={[
        { label: 'RE-RUN SCRAPE', variant: 'ghost', disabled: true, onClick: () => {} },
        { label: 'ADVANCE →', variant: 'primary', onClick: () => navigate(`/jobs/${source}/${jobId}/translate`) },
      ]}
    >
      {url && (
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">URL</p>
          <p className="font-mono text-[9px] text-on-surface break-all leading-relaxed">{url}</p>
        </div>
      )}
    </ControlPanel>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/components/ScrapeControlPanel.tsx
git commit -m "refactor(ui): ScrapeControlPanel uses ControlPanel molecule (B1)"
```

---

## Task 5: Refactor ExtractControlPanel to use ControlPanel molecule

**Files:**
- Modify: `src/features/job-pipeline/components/ExtractControlPanel.tsx`

ExtractControlPanel has custom buttons + selected req display. Use ControlPanel with children for the req inspector.

- [ ] **Step 1: Replace ExtractControlPanel**

```tsx
import { useNavigate } from 'react-router-dom';
import { ControlPanel } from '../../../components/molecules/ControlPanel';
import type { RequirementItem } from '../../../types/api.types';

interface Props {
  source: string;
  jobId: string;
  selectedReq: RequirementItem | null;
  onSave: () => void;
  isSaving: boolean;
}

export function ExtractControlPanel({ source, jobId, selectedReq, onSave, isSaving }: Props) {
  const navigate = useNavigate();

  return (
    <ControlPanel
      title="Extract"
      phaseColor="secondary"
      actions={[
        { label: 'SAVE DRAFT', variant: 'ghost', onClick: onSave, loading: isSaving },
        {
          label: 'COMMIT → MATCH',
          variant: 'primary',
          onClick: () => { onSave(); navigate(`/jobs/${source}/${jobId}/match`); },
        },
      ]}
      shortcuts={[
        { keys: ['Ctrl', 'S'], label: 'Save draft' },
        { keys: ['Ctrl', 'Enter'], label: 'Commit + go to match' },
      ]}
    >
      {selectedReq ? (
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase mb-2">Selected Req</p>
          <pre className="bg-surface-container border border-outline/20 p-2 font-mono text-[9px] text-on-surface overflow-auto whitespace-pre-wrap">
            {JSON.stringify(selectedReq, null, 2)}
          </pre>
        </div>
      ) : (
        <p className="font-mono text-[10px] text-on-muted uppercase">Click a requirement to inspect</p>
      )}
    </ControlPanel>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/components/ExtractControlPanel.tsx
git commit -m "refactor(ui): ExtractControlPanel uses ControlPanel molecule (B2)"
```

---

## Task 6: Refactor MatchControlPanel to use ControlPanel molecule

**Files:**
- Modify: `src/features/job-pipeline/components/MatchControlPanel.tsx`

MatchControlPanel has complex detail views (RequirementDetail, ProfileDetail, EdgeDetail). Use ControlPanel with `children` for these detail components.

- [ ] **Step 1: Replace MatchControlPanel**

Keep the local detail sub-components (ScoreBar, RequirementDetail, ProfileDetail, EdgeDetail) as internal helpers. Use ControlPanel as the shell.

```tsx
import { cn } from '../../../utils/cn';
import { ControlPanel } from '../../../components/molecules/ControlPanel';
import type { GraphNode, GraphEdge } from '../../../types/api.types';

interface Props {
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  onOpenDecisionModal: () => void;
  isSaving: boolean;
  onSave: () => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  must: 'bg-error/20 text-error border-error/30',
  should: 'bg-secondary/20 text-secondary border-secondary/30',
  nice_to_have: 'bg-primary/20 text-primary border-primary/30',
};

function ScoreBar({ score }: { score: number }) {
  const color = score >= 0.7 ? 'bg-primary' : score >= 0.3 ? 'bg-secondary' : 'bg-error';
  return (
    <div className="mt-1">
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1 bg-surface-high">
          <div className={cn('h-full', color)} style={{ width: `${score * 100}%` }} />
        </div>
        <span className="font-mono text-[9px] text-on-muted">{Math.round(score * 100)}%</span>
      </div>
    </div>
  );
}

function NodeDetail({ node }: { node: GraphNode }) {
  if (node.kind === 'requirement') {
    const priority = (node as GraphNode & { priority?: string }).priority ?? 'must';
    const score = (node as GraphNode & { score?: number }).score;
    const chipClass = PRIORITY_COLORS[priority] ?? PRIORITY_COLORS['must'];
    return (
      <div className="space-y-3">
        <p className="font-mono text-[10px] text-on-muted uppercase mb-3">Requirement Node</p>
        <div>
          <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Priority</p>
          <span className={cn('inline-block font-mono text-[9px] uppercase tracking-widest border px-1.5 py-0.5', chipClass)}>
            {priority.replace(/_/g, ' ')}
          </span>
        </div>
        <div>
          <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Requirement</p>
          <p className="font-body text-xs text-on-surface leading-relaxed">{node.label}</p>
        </div>
        {score != null && (
          <div>
            <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Best Match Score</p>
            <ScoreBar score={score} />
          </div>
        )}
      </div>
    );
  }
  const parts = node.label.split(':');
  const category = parts[0]?.trim() ?? 'profile';
  const summary = parts.length > 1 ? parts.slice(1).join(':').trim() : node.label;
  return (
    <div className="space-y-3">
      <p className="font-mono text-[10px] text-on-muted uppercase mb-3">Profile Node</p>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Evidence ID</p>
        <p className="font-mono text-[9px] text-primary">{node.id}</p>
      </div>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Category</p>
        <span className="inline-block font-mono text-[9px] uppercase tracking-widest border px-1.5 py-0.5 bg-primary/10 text-primary border-primary/30">
          {category}
        </span>
      </div>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Summary</p>
        <p className="font-body text-xs text-on-surface leading-relaxed">{summary}</p>
      </div>
    </div>
  );
}

function EdgeDetail({ edge }: { edge: GraphEdge }) {
  const score = edge.score ?? 0;
  return (
    <div className="space-y-3">
      <p className="font-mono text-[10px] text-on-muted uppercase mb-3">Selected Edge</p>
      <div>
        <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Match Score</p>
        <ScoreBar score={score} />
      </div>
      {edge.reasoning && (
        <div>
          <p className="font-mono text-[9px] text-on-muted uppercase mb-1">Reasoning</p>
          <p className="font-body text-xs text-on-surface leading-relaxed">{edge.reasoning}</p>
        </div>
      )}
    </div>
  );
}

export function MatchControlPanel({ selectedNode, selectedEdge, onOpenDecisionModal, isSaving, onSave }: Props) {
  return (
    <ControlPanel
      title="Match"
      phaseColor="secondary"
      actions={[
        { label: 'SAVE (Ctrl+S)', variant: 'ghost', onClick: onSave, loading: isSaving },
        { label: 'COMMIT MATCH (Ctrl+Enter)', variant: 'primary', onClick: onOpenDecisionModal },
      ]}
    >
      {selectedNode
        ? <NodeDetail node={selectedNode} />
        : selectedEdge
          ? <EdgeDetail edge={selectedEdge} />
          : <p className="font-mono text-[10px] text-on-muted uppercase">Click a node or edge</p>
      }
    </ControlPanel>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/components/MatchControlPanel.tsx
git commit -m "refactor(ui): MatchControlPanel uses ControlPanel molecule (B3)"
```

---

## Task 7: Add onConnect to GraphCanvas + refactor MatchGraphCanvas

**Files:**
- Modify: `src/components/organisms/GraphCanvas.tsx`
- Modify: `src/features/job-pipeline/components/MatchGraphCanvas.tsx`

GraphCanvas needs `onConnect` support so MatchGraphCanvas can delegate to it.

- [ ] **Step 1: Add onConnect to GraphCanvas interface and wiring**

In `GraphCanvas.tsx`, add to Props:
```ts
onConnect?: (connection: { source: string; target: string }) => void;
```
And add to ReactFlow props:
```tsx
import { addEdge, type Connection } from '@xyflow/react';
// ...
onConnect={onConnect ? (conn: Connection) => {
  if (conn.source && conn.target) onConnect({ source: conn.source, target: conn.target });
} : undefined}
```

- [ ] **Step 2: Refactor MatchGraphCanvas to use GraphCanvas**

MatchGraphCanvas delegates node/edge data transformation and layout to GraphCanvas, but passes its custom nodeTypes/edgeTypes and uses GraphCanvas's onConnect.

```tsx
import { useMemo } from 'react';
import { GraphCanvas } from '../../../components/organisms/GraphCanvas';
import { RequirementNode } from './RequirementNode';
import { ProfileNode } from './ProfileNode';
import { EdgeScoreBadge } from './EdgeScoreBadge';
import type { GraphNode, GraphEdge } from '../../../types/api.types';

const MATCH_NODE_TYPES = { requirement: RequirementNode, profile: ProfileNode };
const MATCH_EDGE_TYPES = { scoreEdge: EdgeScoreBadge };

interface Props {
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  onNodeClick: (node: GraphNode) => void;
  onEdgeClick: (edge: GraphEdge) => void;
  onAddEdge: (connection: { source: string; target: string }) => void;
  searchQuery: string;
  focusedNodeId: string | null;
}

export function MatchGraphCanvas({
  graphNodes, graphEdges, onNodeClick, onEdgeClick, onAddEdge, searchQuery, focusedNodeId,
}: Props) {
  const reqScores = useMemo(() => {
    const scores: Record<string, number> = {};
    graphEdges.forEach(e => {
      const s = e.score ?? 0;
      if (!scores[e.target] || s > scores[e.target]) scores[e.target] = s;
    });
    return scores;
  }, [graphEdges]);

  const nodes = useMemo(() => {
    const q = searchQuery.toLowerCase();
    return graphNodes.map(n => {
      const dimmed = q.length > 0 && !n.label.toLowerCase().includes(q);
      const highlighted = (q.length > 0 && n.label.toLowerCase().includes(q)) || focusedNodeId === n.id;
      return {
        id: n.id,
        label: n.label,
        type: n.kind === 'requirement' ? 'requirement' : 'profile',
        data: {
          score: n.kind === 'requirement' ? (reqScores[n.id] ?? 0) : undefined,
          dimmed,
          highlighted,
        },
      };
    });
  }, [graphNodes, reqScores, searchQuery, focusedNodeId]);

  const edges = useMemo(() => graphEdges.map((e, i) => ({
    id: `edge-${i}`,
    source: e.source,
    target: e.target,
    score: e.score,
    data: { score: e.score, reasoning: e.reasoning, edgeType: 'llm' as const },
  })), [graphEdges]);

  return (
    <GraphCanvas
      nodes={nodes}
      edges={edges}
      nodeTypes={MATCH_NODE_TYPES}
      edgeTypes={MATCH_EDGE_TYPES}
      layout="LR"
      direction="LR"
      showControls={true}
      onNodeClick={node => {
        const gn = graphNodes.find(n => n.id === node.id);
        if (gn) onNodeClick(gn);
      }}
      onEdgeClick={edge => {
        const ge = graphEdges.find((_, i) => `edge-${i}` === edge.id);
        if (ge) onEdgeClick(ge);
      }}
      onConnect={onAddEdge}
    />
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 4: Commit**

```bash
git add apps/review-workbench/src/components/organisms/GraphCanvas.tsx \
        apps/review-workbench/src/features/job-pipeline/components/MatchGraphCanvas.tsx
git commit -m "refactor(ui): MatchGraphCanvas uses GraphCanvas organism (B3)"
```

---

## Task 8: Refactor ExplorerTree to use FileTree

**Files:**
- Modify: `src/features/explorer/components/ExplorerTree.tsx`

ExplorerTree and FileTree are nearly identical in structure. ExplorerTree uses `ExplorerEntry` type, FileTree uses `FileTreeNode`. Since they share the same shape (`name, path, is_dir, extension, child_count`), ExplorerTree can delegate to FileTree directly.

- [ ] **Step 1: Replace ExplorerTree with FileTree delegation**

```tsx
import { FileTree, type FileTreeNode } from '../../../components/organisms/FileTree';
import type { ExplorerEntry } from '../../../types/api.types';

interface Props {
  entries: ExplorerEntry[];
  activePath: string;
  onSelect: (path: string) => void;
  onLoadChildren?: (path: string) => void;
  childrenMap?: Record<string, ExplorerEntry[]>;
  indent?: number;
}

function toFileNodes(entries: ExplorerEntry[]): FileTreeNode[] {
  return entries.map(e => ({
    name: e.name,
    path: e.path,
    is_dir: e.is_dir,
    extension: e.extension,
    child_count: e.child_count,
  }));
}

export function ExplorerTree({ entries, activePath, onSelect, onLoadChildren, childrenMap = {}, indent = 0 }: Props) {
  const fileNodes = toFileNodes(entries);
  const fileChildrenMap: Record<string, FileTreeNode[]> = {};
  for (const [key, val] of Object.entries(childrenMap)) {
    fileChildrenMap[key] = toFileNodes(val);
  }

  return (
    <FileTree
      nodes={fileNodes}
      currentPath={activePath}
      onNavigate={path => onLoadChildren?.(path)}
      onFileSelect={onSelect}
      childrenMap={fileChildrenMap}
      indent={indent}
    />
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/explorer/components/ExplorerTree.tsx
git commit -m "refactor(ui): ExplorerTree delegates to FileTree organism (A2)"
```

---

## Task 9: Refactor JsonPreview and MarkdownPreview to use IntelligentEditor

**Files:**
- Modify: `src/features/explorer/components/JsonPreview.tsx`
- Modify: `src/features/explorer/components/MarkdownPreview.tsx`

Both components render read-only text. IntelligentEditor (fold mode) with respective language provides syntax highlighting + fold gutter.

- [ ] **Step 1: Replace JsonPreview**

```tsx
import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';

interface Props { content: string; }

export function JsonPreview({ content }: Props) {
  return (
    <div className="h-full overflow-hidden">
      <IntelligentEditor mode="fold" content={content} language="json" readOnly />
    </div>
  );
}
```

- [ ] **Step 2: Replace MarkdownPreview**

```tsx
import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';

interface Props { content: string; }

export function MarkdownPreview({ content }: Props) {
  return (
    <div className="h-full overflow-hidden">
      <IntelligentEditor mode="fold" content={content} language="markdown" readOnly />
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 4: Commit**

```bash
git add apps/review-workbench/src/features/explorer/components/JsonPreview.tsx \
        apps/review-workbench/src/features/explorer/components/MarkdownPreview.tsx
git commit -m "refactor(ui): JsonPreview + MarkdownPreview use IntelligentEditor (A2 fold)"
```

---

## Task 10: Refactor CvGraphCanvas to use GraphCanvas

**Files:**
- Read and modify: `src/features/base-cv/components/CvGraphCanvas.tsx`

CvGraphCanvas uses ReactFlow directly. Read the file first to understand node positioning strategy (likely manual/DnD-based). Then wrap the ReactFlow portion with GraphCanvas using `layout='manual'` and the existing custom nodeTypes.

- [ ] **Step 1: Read CvGraphCanvas**

```bash
cat apps/review-workbench/src/features/base-cv/components/CvGraphCanvas.tsx
```

- [ ] **Step 2: Identify what GraphCanvas replaces**

CvGraphCanvas likely uses `ReactFlow` directly. GraphCanvas with `layout='manual'` passes through positions as-is. Identify:
- Custom nodeTypes → pass to GraphCanvas's `nodeTypes` prop
- `onConnect` → pass via GraphCanvas's `onConnect` prop
- Any other ReactFlow props that GraphCanvas exposes

- [ ] **Step 3: Refactor CvGraphCanvas to use GraphCanvas**

Replace the internal `ReactFlow` component with `GraphCanvas` using `layout='manual'`. Keep DnD wrappers unchanged (they're outside ReactFlow).

Convert CvEntry/CvSkill data to the generic `GraphNode[]` and `GraphEdge[]` shapes expected by GraphCanvas.

- [ ] **Step 4: Verify build**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 5: Commit**

```bash
git add apps/review-workbench/src/features/base-cv/components/CvGraphCanvas.tsx
git commit -m "refactor(ui): CvGraphCanvas uses GraphCanvas organism (A3)"
```

---

## Task 11: Final build verification

- [ ] **Step 1: Full TypeScript check**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npx tsc --noEmit 2>&1
```

Expected: no errors.

- [ ] **Step 2: Dev server smoke test**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench && npm run dev &
sleep 5 && curl -s http://localhost:5173 | head -5
```

Expected: HTML response (app running).

---

## Task 12: TestSprite E2E

**Run TestSprite to validate all refactored pages.**

- [ ] **Step 1: Check TestSprite account**

Use `mcp__TestSprite__testsprite_check_account_info` tool.

- [ ] **Step 2: Generate code summary for TestSprite**

Use `mcp__TestSprite__testsprite_generate_code_summary` — this gives TestSprite context about the current codebase.

- [ ] **Step 3: Generate/update frontend test plan**

Use `mcp__TestSprite__testsprite_generate_frontend_test_plan` targeting the refactored pages:
- B1: `/jobs/tu_berlin/201397/scrape`
- B1b: `/jobs/tu_berlin/201397/translate`
- B2: `/jobs/tu_berlin/201397/extract`
- B3: `/jobs/tu_berlin/201397/match`
- B4: `/jobs/tu_berlin/201397/sculpt`
- A2: `/explorer`
- A3: `/cv`

- [ ] **Step 4: Execute tests**

Use `mcp__TestSprite__testsprite_generate_code_and_execute` to run the tests.

- [ ] **Step 5: Review results**

Use `mcp__TestSprite__testsprite_open_test_result_dashboard` to inspect failures.

---

## Task 13: Update checklist + changelog

- [ ] **Step 1: Update index_checklist.md**

Add new section for component_map compliance phase:

```markdown
### Fase 11 — Component Map Compliance ✅
- [x] `IntelligentEditor` — fixed decorations, added `onSpanSelect`
- [x] `SourceTextPane` → uses IntelligentEditor (tag-hover)
- [x] `DocumentEditor` → uses IntelligentEditor (fold)
- [x] `ScrapeControlPanel` → uses ControlPanel molecule
- [x] `ExtractControlPanel` → uses ControlPanel molecule
- [x] `MatchControlPanel` → uses ControlPanel molecule
- [x] `GraphCanvas` → added onConnect support
- [x] `MatchGraphCanvas` → uses GraphCanvas organism
- [x] `ExplorerTree` → delegates to FileTree organism
- [x] `JsonPreview` → uses IntelligentEditor (fold/json)
- [x] `MarkdownPreview` → uses IntelligentEditor (fold/markdown)
- [x] `CvGraphCanvas` → uses GraphCanvas organism (manual layout)
- [x] E2E tests — TestSprite suite passing
```

- [ ] **Step 2: Add changelog entry**

In `changelog.md`:
```markdown
## 2026-03-23

- Fase 11 Component Map Compliance: refactored all feature components to use
  organisms and molecules from component_map.md. IntelligentEditor now has
  working decorations (StateField) and onSpanSelect support. All control panels
  use generic ControlPanel molecule. MatchGraphCanvas, ExplorerTree, and
  CvGraphCanvas delegate to organism internals. E2E suite validated with TestSprite.
```

- [ ] **Step 3: Final commit**

```bash
cd /home/jp/phd-workspaces/dev/.worktrees/ui-redesign
git add plan/index_checklist.md changelog.md
git commit -m "docs: update checklist + changelog for Fase 11 component_map compliance"
```
