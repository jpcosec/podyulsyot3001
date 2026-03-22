import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useViewDocuments } from '../../features/job-pipeline/api/useViewDocuments';
import { useDocumentSave } from '../../features/job-pipeline/api/useDocumentSave';
import { useGateDecide } from '../../features/job-pipeline/api/useGateDecide';
import { SplitPane } from '../../components/molecules/SplitPane';
import { DocumentTabs, type DocKey } from '../../features/job-pipeline/components/DocumentTabs';
import { DocumentEditor } from '../../features/job-pipeline/components/DocumentEditor';
import { ContextPanel } from '../../features/job-pipeline/components/ContextPanel';
import { DocApproveBar } from '../../features/job-pipeline/components/DocApproveBar';
import { RegenModal } from '../../features/job-pipeline/components/RegenModal';
import { Spinner } from '../../components/atoms/Spinner';

type DocState = { content: string; isDirty: boolean; isApproved: boolean };

export function GenerateDocuments() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const navigate = useNavigate();

  const docsQuery = useViewDocuments(source!, jobId!);
  const saveDoc = useDocumentSave(source!, jobId!);
  const gateDecide = useGateDecide(source!, jobId!, 'review_match');

  const [activeTab, setActiveTab] = useState<DocKey>('cv');
  const [docs, setDocs] = useState<Record<DocKey, DocState>>({
    cv: { content: '', isDirty: false, isApproved: false },
    motivation_letter: { content: '', isDirty: false, isApproved: false },
    application_email: { content: '', isDirty: false, isApproved: false },
  });
  const [isRegenOpen, setIsRegenOpen] = useState(false);

  useEffect(() => {
    if (docsQuery.data?.view === 'documents') {
      const { documents } = docsQuery.data.data;
      setDocs({
        cv: { content: documents.cv, isDirty: false, isApproved: false },
        motivation_letter: { content: documents.motivation_letter, isDirty: false, isApproved: false },
        application_email: { content: documents.application_email, isDirty: false, isApproved: false },
      });
    }
  }, [docsQuery.data]);

  const handleSave = useCallback(() => {
    const doc = docs[activeTab];
    saveDoc.mutate({ docKey: activeTab, markdown: doc.content }, {
      onSuccess: () => setDocs(prev => ({
        ...prev,
        [activeTab]: { ...prev[activeTab], isDirty: false },
      })),
    });
  }, [activeTab, docs, saveDoc]);

  const handleApprove = useCallback(() => {
    setDocs(prev => ({
      ...prev,
      [activeTab]: { ...prev[activeTab], isApproved: true },
    }));
  }, [activeTab]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 's') { e.preventDefault(); handleSave(); }
      if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); handleApprove(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSave, handleApprove]);

  const handleChange = (value: string) => {
    setDocs(prev => ({ ...prev, [activeTab]: { ...prev[activeTab], content: value, isDirty: true } }));
  };

  const handleApproveAll = () => {
    gateDecide.mutate({ decision: 'approve' }, {
      onSuccess: () => navigate(`/jobs/${source}/${jobId}/deployment`),
    });
  };

  const handleRegen = (feedback: string) => {
    gateDecide.mutate(
      { decision: 'request_regeneration', feedback: feedback ? [feedback] : [] },
      { onSuccess: () => { setIsRegenOpen(false); } },
    );
  };

  if (docsQuery.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }
  if (docsQuery.isError || !docsQuery.data || docsQuery.data.view !== 'documents') {
    return <div className="p-6"><p className="font-mono text-error text-sm">DOCUMENTS_NOT_FOUND</p></div>;
  }

  const { nodes, edges } = docsQuery.data.data;
  const tabStates = {
    cv: { isDirty: docs.cv.isDirty, isApproved: docs.cv.isApproved },
    motivation_letter: { isDirty: docs.motivation_letter.isDirty, isApproved: docs.motivation_letter.isApproved },
    application_email: { isDirty: docs.application_email.isDirty, isApproved: docs.application_email.isApproved },
  };

  return (
    <div className="flex flex-col h-full">
      <SplitPane orientation="horizontal" defaultSizes={[70, 30]}>
        {/* Left: Editor */}
        <div className="flex flex-col h-full overflow-hidden">
          <DocumentTabs activeTab={activeTab} tabStates={tabStates} onTabChange={setActiveTab} />
          <div className="flex-1 overflow-hidden">
            <DocumentEditor content={docs[activeTab].content} onChange={handleChange} />
          </div>
          <DocApproveBar
            onSave={handleSave}
            onApprove={handleApprove}
            isSaving={saveDoc.isPending}
            isApproved={docs[activeTab].isApproved}
            activeTab={activeTab}
          />
        </div>
        {/* Right: Context */}
        <ContextPanel
          nodes={nodes}
          edges={edges}
          onRequestRegen={() => setIsRegenOpen(true)}
          onApproveAll={handleApproveAll}
          isLoading={gateDecide.isPending}
        />
      </SplitPane>

      <RegenModal
        isOpen={isRegenOpen}
        onClose={() => setIsRegenOpen(false)}
        onConfirm={handleRegen}
        isLoading={gateDecide.isPending}
      />
    </div>
  );
}
