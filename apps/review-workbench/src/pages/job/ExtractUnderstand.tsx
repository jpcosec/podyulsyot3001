import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useViewExtract } from '../../features/job-pipeline/api/useViewExtract';
import { useEditorState } from '../../features/job-pipeline/api/useEditorState';
import { SplitPane } from '../../components/molecules/SplitPane';
import { SourceTextPane } from '../../features/job-pipeline/components/SourceTextPane';
import { RequirementList } from '../../features/job-pipeline/components/RequirementList';
import { ExtractControlPanel } from '../../features/job-pipeline/components/ExtractControlPanel';
import { Spinner } from '../../components/atoms/Spinner';
import type { RequirementItem } from '../../types/api.types';

export function ExtractUnderstand() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const extractQuery = useViewExtract(source!, jobId!);
  const saveState = useEditorState(source!, jobId!, 'extract_understand');

  const [requirements, setRequirements] = useState<RequirementItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredReq, setHoveredReq] = useState<RequirementItem | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (extractQuery.data?.view === 'extract') {
      setRequirements(extractQuery.data.data.requirements);
    }
  }, [extractQuery.data]);

  const handleSave = useCallback(() => {
    saveState.mutate({ state: { requirements } });
    setIsDirty(false);
  }, [saveState, requirements]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 's') { e.preventDefault(); handleSave(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSave]);

  const handleChange = (id: string, field: 'text' | 'priority', value: string) => {
    setRequirements(prev => prev.map(r => r.id === id ? { ...r, [field]: value } : r));
    setIsDirty(true);
  };

  const handleDelete = (id: string) => {
    const req = requirements.find(r => r.id === id);
    if (req?.priority === 'must' && !window.confirm(`Delete MUST requirement "${req.text.slice(0, 40)}..."?`)) return;
    setRequirements(prev => prev.filter(r => r.id !== id));
    setIsDirty(true);
  };

  const handleAdd = () => {
    const newReq: RequirementItem = {
      id: `req_${Date.now()}`,
      text: 'New requirement',
      priority: 'nice',
      spans: [],
      text_span: null,
    };
    setRequirements(prev => [...prev, newReq]);
    setSelectedId(newReq.id);
    setIsDirty(true);
  };

  if (extractQuery.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }
  if (extractQuery.isError || !extractQuery.data || extractQuery.data.view !== 'extract') {
    return <div className="p-6"><p className="font-mono text-error text-sm">EXTRACT_DATA_NOT_FOUND</p></div>;
  }

  const { source_markdown } = extractQuery.data.data;
  const selectedReq = requirements.find(r => r.id === selectedId) ?? null;
  const highlight = (hoveredReq ?? selectedReq)?.text_span ?? null;

  return (
    <div className="flex h-full">
      <div className="flex-1 min-w-0">
        <SplitPane orientation="horizontal" defaultSizes={[50, 50]}>
          <SourceTextPane markdown={source_markdown} highlight={highlight} />
          <RequirementList
            requirements={requirements}
            selectedId={selectedId}
            onSelect={id => { setSelectedId(id); setHoveredReq(null); }}
            onHover={setHoveredReq}
            onChange={handleChange}
            onDelete={handleDelete}
            onAdd={handleAdd}
          />
        </SplitPane>
      </div>
      <ExtractControlPanel
        source={source!}
        jobId={jobId!}
        selectedReq={selectedReq}
        onSave={handleSave}
        isSaving={saveState.isPending}
      />
    </div>
  );
}
