import { useState, useEffect, useCallback } from 'react';
import { useCvProfileGraph, useSaveCvGraph } from '../../features/base-cv/api/useCvProfileGraph';
import { CvGraphCanvas } from '../../features/base-cv/components/CvGraphCanvas';
import { NodeInspector } from '../../features/base-cv/components/NodeInspector';
import { ProfileStats } from '../../features/base-cv/components/ProfileStats';
import { SkillPalette } from '../../features/base-cv/components/SkillPalette';
import { Spinner } from '../../components/atoms/Spinner';
import { nextDescriptionWeight } from '../../features/base-cv/lib/mastery-scale';
import type { CvEntry, CvSkill, CvDemonstratesEdge, CvProfileGraphPayload } from '../../types/api.types';

type NodeType = 'entry' | 'skill' | 'group';

function uniqueId(prefix: string): string {
  return `${prefix}:${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

export function BaseCvEditor() {
  const query = useCvProfileGraph();
  const saveMutation = useSaveCvGraph();

  const [editedEntries, setEditedEntries] = useState<CvEntry[] | null>(null);
  const [editedSkills, setEditedSkills] = useState<CvSkill[] | null>(null);
  const [editedDemonstrates, setEditedDemonstrates] = useState<CvDemonstratesEdge[] | null>(null);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<NodeType | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => new Set());
  const [focusedEntryId, setFocusedEntryId] = useState('');
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [selectedGroupCategory, setSelectedGroupCategory] = useState<string | null>(null);
  const [activeDropzoneCategory, setActiveDropzoneCategory] = useState<string | null>(null);

  const entries = editedEntries ?? query.data?.entries ?? [];
  const skills = editedSkills ?? query.data?.skills ?? [];
  const demonstrates = editedDemonstrates ?? query.data?.demonstrates ?? [];

  // ── Node click ───────────────────────────────────────────────────────────

  const handleNodeClick = useCallback((id: string, type: NodeType) => {
    if (type === 'group') {
      // group clicks are handled by group header — here just clear selection
      return;
    }
    setSelectedNodeId(id);
    setSelectedNodeType(type);
    setSelectedGroupCategory(null);
    if (type === 'skill') {
      setSelectedSkillId(id);
    }
  }, []);

  // ── Group operations ─────────────────────────────────────────────────────

  const handleToggleGroup = useCallback((category: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }, []);

  const handleSelectGroup = useCallback((category: string) => {
    setSelectedGroupCategory(category);
    setSelectedNodeId(null);
    setSelectedNodeType(null);
  }, []);

  // ── Entry operations ─────────────────────────────────────────────────────

  const handleAddEntry = useCallback((category: string) => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      const newEntry: CvEntry = {
        id: uniqueId('entry'),
        category,
        essential: false,
        fields: { title: 'New entry' },
        descriptions: [],
      };
      return [...base, newEntry];
    });
    setActiveDropzoneCategory(category);
  }, [query.data]);

  const handleToggleExpand = useCallback((entryId: string) => {
    setFocusedEntryId(prev => prev === entryId ? '' : entryId);
  }, []);

  const handleUpdateCategory = useCallback((entryId: string, category: string) => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      return base.map(e => e.id === entryId ? { ...e, category } : e);
    });
  }, [query.data]);

  const handleToggleEssentialEntry = useCallback((entryId: string, next: boolean) => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      return base.map(e => e.id === entryId ? { ...e, essential: next } : e);
    });
  }, [query.data]);

  const handleUpdateDescription = useCallback((entryId: string, key: string, text: string) => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      return base.map(e => {
        if (e.id !== entryId) return e;
        return {
          ...e,
          descriptions: e.descriptions.map(d => d.key === key ? { ...d, text } : d),
        };
      });
    });
  }, [query.data]);

  const handleAddDescription = useCallback((entryId: string) => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      return base.map(e => {
        if (e.id !== entryId) return e;
        const weight = nextDescriptionWeight(e.descriptions.length);
        const key = `desc_${e.descriptions.length + 1}`;
        return {
          ...e,
          descriptions: [...e.descriptions, { key, text: '', weight }],
        };
      });
    });
  }, [query.data]);

  const handleMoveEntry = useCallback((entryId: string, direction: 'up' | 'down') => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      const entry = base.find(e => e.id === entryId);
      if (!entry) return base;
      const category = entry.category;
      const categoryEntries = base.filter(e => e.category === category);
      const currentIndex = categoryEntries.findIndex(e => e.id === entryId);
      const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
      if (targetIndex < 0 || targetIndex >= categoryEntries.length) return base;

      // Swap in category slice
      const reordered = [...categoryEntries];
      const tmp = reordered[currentIndex]!;
      reordered[currentIndex] = reordered[targetIndex]!;
      reordered[targetIndex] = tmp;

      let catCursor = 0;
      return base.map(e => {
        if (e.category !== category) return e;
        return reordered[catCursor++]!;
      });
    });
  }, [query.data]);

  // ── Skill operations ─────────────────────────────────────────────────────

  const handleAddSkill = useCallback(() => {
    setEditedSkills(prev => {
      const base = prev ?? query.data!.skills;
      const newSkill: CvSkill = {
        id: uniqueId('skill'),
        label: 'New skill',
        category: 'uncategorized',
        essential: false,
        level: 'intermediate',
        meta: {},
      };
      return [...base, newSkill];
    });
  }, [query.data]);

  const handleSelectSkill = useCallback((id: string) => {
    setSelectedSkillId(id);
    setSelectedNodeId(id);
    setSelectedNodeType('skill');
    setSelectedGroupCategory(null);
  }, []);

  const handleEntryChange = useCallback((id: string, field: string, value: string) => {
    setEditedEntries(prev => {
      const base = prev ?? query.data!.entries;
      return base.map(e => e.id === id ? { ...e, fields: { ...e.fields, [field]: value } } : e);
    });
  }, [query.data]);

  const handleSkillChange = useCallback((id: string, field: 'label' | 'level', value: string) => {
    setEditedSkills(prev => {
      const base = prev ?? query.data!.skills;
      return base.map(s => s.id === id ? { ...s, [field]: value || null } : s);
    });
  }, [query.data]);

  const handleToggleEssential = useCallback((id: string, type: 'entry' | 'skill') => {
    if (type === 'entry') {
      setEditedEntries(prev => {
        const base = prev ?? query.data!.entries;
        return base.map(e => e.id === id ? { ...e, essential: !e.essential } : e);
      });
    } else {
      setEditedSkills(prev => {
        const base = prev ?? query.data!.skills;
        return base.map(s => s.id === id ? { ...s, essential: !s.essential } : s);
      });
    }
  }, [query.data]);

  // ── Edge operations ──────────────────────────────────────────────────────

  const handleConnectEdge = useCallback((sourceEntry: string, targetSkill: string) => {
    setEditedDemonstrates(prev => {
      const base = prev ?? query.data?.demonstrates ?? [];
      const alreadyExists = base.some(
        d => d.source === sourceEntry && d.target === targetSkill
      );
      if (alreadyExists) return base;
      const newEdge: CvDemonstratesEdge = {
        id: uniqueId('demonstrates'),
        source: sourceEntry,
        target: targetSkill,
        description_keys: [],
      };
      return [...base, newEdge];
    });
  }, [query.data]);

  // ── Save ─────────────────────────────────────────────────────────────────

  const handleSave = useCallback(() => {
    if (!query.data) return;
    const payload: CvProfileGraphPayload = {
      ...query.data,
      entries,
      skills,
      demonstrates,
    };
    saveMutation.mutate(payload);
  }, [query.data, entries, skills, demonstrates, saveMutation]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      setSelectedNodeId(null);
      setSelectedNodeType(null);
      setSelectedGroupCategory(null);
      setFocusedEntryId('');
    }
  }, [handleSave]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // ── Derived state for sidebar ─────────────────────────────────────────────

  const relatedSkillIds = new Set(
    demonstrates
      .filter(d => d.source === focusedEntryId)
      .map(d => d.target)
  );

  const showSkillPalette = Boolean(focusedEntryId);
  const showGroupInspector = Boolean(selectedGroupCategory);
  const showNodeInspector = selectedNodeType === 'entry' || selectedNodeType === 'skill';
  const showStats = !showGroupInspector && !showNodeInspector && !showSkillPalette;

  // ── Render ────────────────────────────────────────────────────────────────

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

  return (
    <div className="flex h-full">
      <div className="flex-1 min-w-0">
        <CvGraphCanvas
          entries={entries}
          skills={skills}
          demonstrates={demonstrates}
          expandedGroups={expandedGroups}
          focusedEntryId={focusedEntryId}
          selectedNodeId={selectedNodeId}
          activeDropzoneCategory={activeDropzoneCategory}
          selectedGroupCategory={selectedGroupCategory}
          onNodeClick={handleNodeClick}
          onToggleGroup={handleToggleGroup}
          onSelectGroup={handleSelectGroup}
          onAddEntry={handleAddEntry}
          onAddSkill={handleAddSkill}
          onToggleExpand={handleToggleExpand}
          onUpdateCategory={handleUpdateCategory}
          onToggleEssential={handleToggleEssentialEntry}
          onUpdateDescription={handleUpdateDescription}
          onAddDescription={handleAddDescription}
          onSelectSkill={handleSelectSkill}
          onConnect={handleConnectEdge}
        />
      </div>

      <aside className="w-80 bg-surface border-l border-outline/20 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-hidden">
          {showGroupInspector && (
            <NodeInspector
              entryId={null}
              skillId={null}
              entries={entries}
              skills={skills}
              onEntryChange={handleEntryChange}
              onSkillChange={handleSkillChange}
              onToggleEssential={handleToggleEssential}
              groupCategory={selectedGroupCategory}
              onMoveEntry={handleMoveEntry}
            />
          )}

          {!showGroupInspector && showNodeInspector && (
            <NodeInspector
              entryId={selectedNodeType === 'entry' ? selectedNodeId : null}
              skillId={selectedNodeType === 'skill' ? selectedNodeId : null}
              entries={entries}
              skills={skills}
              onEntryChange={handleEntryChange}
              onSkillChange={handleSkillChange}
              onToggleEssential={handleToggleEssential}
              groupCategory={null}
              onMoveEntry={handleMoveEntry}
            />
          )}

          {!showGroupInspector && !showNodeInspector && showSkillPalette && (
            <SkillPalette
              skills={skills}
              relatedSkillIds={relatedSkillIds}
              selectedSkillId={selectedSkillId}
              focusedEntryId={focusedEntryId}
              onSelectSkill={handleSelectSkill}
              onAddSkill={handleAddSkill}
              onSkillChange={handleSkillChange}
              onToggleSkillEssential={id => handleToggleEssential(id, 'skill')}
            />
          )}

          {showStats && (
            <ProfileStats entries={entries} skills={skills} />
          )}
        </div>

        <div className="shrink-0 p-3 border-t border-outline/20 flex items-center justify-between">
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
