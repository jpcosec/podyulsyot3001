import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useViewMatch } from '../../features/job-pipeline/api/useViewMatch';
import { useEvidenceBank } from '../../features/job-pipeline/api/useEvidenceBank';
import { useGateDecide } from '../../features/job-pipeline/api/useGateDecide';
import { useEditorState } from '../../features/job-pipeline/api/useEditorState';
import { MatchGraphCanvas } from '../../features/job-pipeline/components/MatchGraphCanvas';
import { EvidenceBankPanel } from '../../features/job-pipeline/components/EvidenceBankPanel';
import { MatchControlPanel } from '../../features/job-pipeline/components/MatchControlPanel';
import { MatchDecisionModal } from '../../features/job-pipeline/components/MatchDecisionModal';
import { ShortcutsModal } from '../../components/atoms/ShortcutsModal';
import { Spinner } from '../../components/atoms/Spinner';
import type { GraphNode, GraphEdge, GateDecisionPayload } from '../../types/api.types';

const SHORTCUTS = [
  { key: 'Ctrl+S',            action: 'Save manual edges' },
  { key: 'Ctrl+Enter',        action: 'Open commit modal' },
  { key: 'Ctrl+Z',            action: 'Undo last manual edge' },
  { key: 'Ctrl+Y / Ctrl+Shift+Z', action: 'Redo' },
  { key: '/',                 action: 'Focus search bar' },
  { key: 'Arrow Up/Down',     action: 'Cycle through nodes' },
  { key: '?',                 action: 'Show this reference' },
  { key: 'Escape',            action: 'Clear search / close modal / deselect' },
];

export function Match() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const matchQuery = useViewMatch(source!, jobId!);
  const evidenceQuery = useEvidenceBank(source!, jobId!);
  const saveState = useEditorState(source!, jobId!, 'match');
  const gateDecide = useGateDecide(source!, jobId!, 'review_match');

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Undo/redo history stack for manual edges
  const [manualEdgesHistory, setManualEdgesHistory] = useState<{ source: string; target: string }[][]>([[]]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const manualEdges = manualEdgesHistory[historyIndex] ?? [];

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const searchRef = useRef<HTMLInputElement>(null);

  // Keyboard navigation
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  // Shortcuts modal
  const [showShortcuts, setShowShortcuts] = useState(false);

  const handleAddEdge = useCallback((conn: { source: string; target: string }) => {
    setManualEdgesHistory(prev => {
      const base = prev.slice(0, historyIndex + 1);
      const next = [...(base[base.length - 1] ?? []), conn];
      return [...base, next];
    });
    setHistoryIndex(prev => prev + 1);
  }, [historyIndex]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const tag = (e.target as HTMLElement).tagName;
    const isInput = tag === 'INPUT' || tag === 'TEXTAREA';

    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      saveState.mutate({ state: { manualEdges } });
      return;
    }
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      setIsModalOpen(true);
      return;
    }
    if (e.ctrlKey && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) {
      e.preventDefault();
      setHistoryIndex(prev => Math.max(0, prev - 1));
      return;
    }
    if (e.ctrlKey && (e.key === 'y' || e.key === 'Y' || (e.key === 'Z' && e.shiftKey))) {
      e.preventDefault();
      setHistoryIndex(prev => Math.min(manualEdgesHistory.length - 1, prev + 1));
      return;
    }
    if (e.key === 'Escape') {
      setSearchQuery('');
      setShowShortcuts(false);
      setSelectedNode(null);
      setSelectedEdge(null);
      return;
    }
    if (!isInput && e.key === '/') {
      e.preventDefault();
      searchRef.current?.focus();
      return;
    }
    if (!isInput && e.key === '?') {
      setShowShortcuts(v => !v);
      return;
    }
  }, [saveState, manualEdges]);

  // Arrow key navigation through visible nodes
  const handleArrowNav = useCallback((e: KeyboardEvent, graphNodes: GraphNode[]) => {
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    const tag = (e.target as HTMLElement).tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;

    const q = searchQuery.toLowerCase();
    const visibleNodes = q
      ? graphNodes.filter(n => n.label.toLowerCase().includes(q))
      : graphNodes;

    if (visibleNodes.length === 0) return;
    e.preventDefault();

    setFocusedNodeId(prev => {
      const idx = visibleNodes.findIndex(n => n.id === prev);
      if (e.key === 'ArrowDown') {
        return visibleNodes[(idx + 1) % visibleNodes.length].id;
      } else {
        return visibleNodes[(idx - 1 + visibleNodes.length) % visibleNodes.length].id;
      }
    });
  }, [searchQuery]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const graphNodes = matchQuery.data?.view === 'match' ? matchQuery.data.data.nodes : [];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => handleArrowNav(e, graphNodes);
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleArrowNav, graphNodes]);

  const handleDecide = (payload: GateDecisionPayload) => {
    gateDecide.mutate(payload, {
      onSuccess: () => setIsModalOpen(false),
    });
  };

  if (matchQuery.isLoading || evidenceQuery.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (matchQuery.isError || !matchQuery.data || matchQuery.data.view !== 'match') {
    return <div className="p-6"><p className="font-mono text-error text-sm">MATCH_DATA_NOT_FOUND</p></div>;
  }

  const { nodes: matchNodes, edges: matchEdges } = matchQuery.data.data;
  const evidenceItems = evidenceQuery.data?.items ?? [];

  return (
    <div className="flex h-full">
      <EvidenceBankPanel items={evidenceItems} />

      <div className="relative flex-1 min-w-0 flex flex-col">
        <div className="shrink-0 flex items-center gap-2 px-3 py-2 border-b border-outline/20 bg-surface">
          <span className="font-mono text-[9px] text-on-muted">SEARCH</span>
          <input
            ref={searchRef}
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Escape' && setSearchQuery('')}
            placeholder="Filter nodes..."
            className="flex-1 bg-transparent border-0 outline-none font-mono text-xs text-on-surface placeholder:text-on-muted/40"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="font-mono text-[10px] text-on-muted/60 hover:text-on-muted"
            >
              ×
            </button>
          )}
          <button
            onClick={() => setShowShortcuts(true)}
            className="font-mono text-[9px] text-on-muted/60 hover:text-on-muted border border-outline/20 px-1.5 py-0.5"
          >
            ?
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <MatchGraphCanvas
            graphNodes={matchNodes}
            graphEdges={matchEdges}
            onNodeClick={node => { setSelectedNode(node); setSelectedEdge(null); }}
            onEdgeClick={edge => { setSelectedEdge(edge); setSelectedNode(null); }}
            onAddEdge={handleAddEdge}
            searchQuery={searchQuery}
            focusedNodeId={focusedNodeId}
          />
        </div>
      </div>

      <MatchControlPanel
        selectedNode={selectedNode}
        selectedEdge={selectedEdge}
        onOpenDecisionModal={() => setIsModalOpen(true)}
        isSaving={saveState.isPending}
        onSave={() => saveState.mutate({ state: { manualEdges } })}
      />

      <MatchDecisionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDecide={handleDecide}
        isLoading={gateDecide.isPending}
      />

      <ShortcutsModal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
        title="Match Keyboard Shortcuts"
        shortcuts={SHORTCUTS}
      />
    </div>
  );
}
