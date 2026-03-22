import { useState, useEffect, useCallback } from 'react';
import { useCvProfileGraph, useSaveCvGraph } from '../../features/base-cv/api/useCvProfileGraph';
import { CvGraphCanvas } from '../../features/base-cv/components/CvGraphCanvas';
import { NodeInspector } from '../../features/base-cv/components/NodeInspector';
import { ProfileStats } from '../../features/base-cv/components/ProfileStats';
import { Spinner } from '../../components/atoms/Spinner';
import type { CvEntry, CvSkill, CvProfileGraphPayload } from '../../types/api.types';

type NodeType = 'entry' | 'skill';

export function BaseCvEditor() {
  const query = useCvProfileGraph();
  const saveMutation = useSaveCvGraph();

  const [entries, setEntries] = useState<CvEntry[]>([]);
  const [skills, setSkills] = useState<CvSkill[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<NodeType | null>(null);

  useEffect(() => {
    if (query.data) {
      setEntries(query.data.entries);
      setSkills(query.data.skills);
    }
  }, [query.data]);

  const handleNodeClick = useCallback((id: string, type: NodeType) => {
    setSelectedNodeId(id);
    setSelectedNodeType(type);
  }, []);

  const handleEntryChange = useCallback((id: string, field: string, value: string) => {
    setEntries(prev => prev.map(e =>
      e.id === id ? { ...e, fields: { ...e.fields, [field]: value } } : e
    ));
  }, []);

  const handleSkillChange = useCallback((id: string, field: 'label' | 'level', value: string) => {
    setSkills(prev => prev.map(s =>
      s.id === id ? { ...s, [field]: value || null } : s
    ));
  }, []);

  const handleToggleEssential = useCallback((id: string, type: NodeType) => {
    if (type === 'entry') {
      setEntries(prev => prev.map(e =>
        e.id === id ? { ...e, essential: !e.essential } : e
      ));
    } else {
      setSkills(prev => prev.map(s =>
        s.id === id ? { ...s, essential: !s.essential } : s
      ));
    }
  }, []);

  const handleSave = useCallback(() => {
    if (!query.data) return;
    const payload: CvProfileGraphPayload = {
      ...query.data,
      entries,
      skills,
    };
    saveMutation.mutate(payload);
  }, [query.data, entries, skills, saveMutation]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      setSelectedNodeId(null);
      setSelectedNodeType(null);
    }
  }, [handleSave]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (query.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (query.isError || !query.data) {
    return (
      <div className="p-6">
        <p className="font-mono text-error text-sm">CV_PROFILE_GRAPH_NOT_FOUND</p>
      </div>
    );
  }

  const { demonstrates } = query.data;
  const hasSelection = selectedNodeId !== null;

  return (
    <div className="flex h-full">
      <div className="flex-1 min-w-0">
        <CvGraphCanvas
          entries={entries}
          skills={skills}
          demonstrates={demonstrates}
          selectedNodeId={selectedNodeId}
          onNodeClick={handleNodeClick}
        />
      </div>

      <aside className="w-80 bg-surface border-l border-outline/20 flex flex-col overflow-hidden">
        {hasSelection ? (
          <NodeInspector
            entryId={selectedNodeType === 'entry' ? selectedNodeId : null}
            skillId={selectedNodeType === 'skill' ? selectedNodeId : null}
            entries={entries}
            skills={skills}
            onEntryChange={handleEntryChange}
            onSkillChange={handleSkillChange}
            onToggleEssential={handleToggleEssential}
          />
        ) : (
          <ProfileStats entries={entries} skills={skills} />
        )}

        <div className="mt-auto p-3 border-t border-outline/20 flex items-center justify-between">
          <span className="font-mono text-[9px] text-on-muted/60">
            {saveMutation.isPending ? 'Saving…' : saveMutation.isSuccess ? 'Saved' : 'Ctrl+S to save'}
          </span>
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="font-mono text-[10px] text-primary border border-primary/40 px-3 py-1 hover:bg-primary/10 disabled:opacity-40 transition-colors"
          >
            Save
          </button>
        </div>
      </aside>
    </div>
  );
}
