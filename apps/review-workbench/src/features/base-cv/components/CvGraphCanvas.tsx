import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type EdgeTypes,
  type NodeTypes,
  type Connection,
} from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import { EntryNode } from './EntryNode';
import { SkillBallNode } from './SkillBallNode';
import { GroupNode } from './GroupNode';
import { ProxyEdge } from './ProxyEdge';
import type { CvEntry, CvSkill, CvDemonstratesEdge } from '../../../types/api.types';
import type { EntryNodeData, GroupNodeData, SkillNodeData } from './types';
import { masteryColorForCategory, resolveMasteryLevel } from '../lib/mastery-scale';

// ── Constants ────────────────────────────────────────────────────────────────

const ENTRY_NODE_WIDTH = 300;
const ENTRY_NODE_HEIGHT = 58;

const ENTRY_CATEGORY_ORDER = [
  'personal_data',
  'contact',
  'legal_status',
  'education',
  'job_experience',
  'internship',
  'publication',
  'project',
  'language_fact',
];

const nodeTypes: NodeTypes = {
  entry: EntryNode,
  skill: SkillBallNode,
  group: GroupNode,
};

const edgeTypes: EdgeTypes = {
  proxy: ProxyEdge,
};

// ── Types ────────────────────────────────────────────────────────────────────

type FlowNodeData = (EntryNodeData | SkillNodeData | GroupNodeData) & Record<string, unknown>;
type FlowNode = Node<FlowNodeData>;
type FlowEdge = Edge<{
  relation: 'demonstrates';
  realSource: string;
  realTarget: string;
  proxy: boolean;
}>;

export interface Props {
  entries: CvEntry[];
  skills: CvSkill[];
  demonstrates: CvDemonstratesEdge[];
  expandedGroups: Set<string>;
  focusedEntryId: string;
  selectedNodeId: string | null;
  activeDropzoneCategory: string | null;
  selectedGroupCategory: string | null;
  onNodeClick: (id: string, type: 'entry' | 'skill' | 'group') => void;
  onToggleGroup: (category: string) => void;
  onSelectGroup: (category: string) => void;
  onAddEntry: (category: string) => void;
  onAddSkill: () => void;
  onToggleExpand: (entryId: string) => void;
  onUpdateCategory: (entryId: string, category: string) => void;
  onToggleEssential: (entryId: string, next: boolean) => void;
  onUpdateDescription: (entryId: string, key: string, text: string) => void;
  onAddDescription: (entryId: string) => void;
  onSelectSkill: (skillId: string) => void;
  onConnect: (sourceEntry: string, targetSkill: string) => void;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function asText(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function displayCategory(value: string): string {
  return value
    .split('_')
    .map(token => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ');
}

function entryLabel(entry: CvEntry): string {
  const role = asText(entry.fields.role);
  const organization = asText(entry.fields.organization);
  const degree = asText(entry.fields.degree);
  const institution = asText(entry.fields.institution);
  const title = asText(entry.fields.title);
  const name = asText(entry.fields.name);
  const fullName = asText(entry.fields.full_name);
  const preferredName = asText(entry.fields.preferred_name);

  if (role) return organization ? `${role} @ ${organization}` : role;
  if (degree) return institution ? `${degree} @ ${institution}` : degree;
  if (title) return title;
  if (name) return name;
  if (preferredName) return preferredName;
  if (fullName) return fullName;
  return displayCategory(entry.category);
}

function orderedCategories(entries: CvEntry[]): string[] {
  const discovered = new Set(entries.map(e => e.category));
  const ordered = ENTRY_CATEGORY_ORDER.filter(c => discovered.has(c));
  for (const c of discovered) {
    if (!ordered.includes(c)) ordered.push(c);
  }
  return ordered;
}

function asDimension(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function toSkillMeta(value: Record<string, unknown>): Record<string, unknown> {
  return value;
}

// ── buildGraphViewNodes ───────────────────────────────────────────────────────

interface BuildParams {
  entries: CvEntry[];
  skills: CvSkill[];
  demonstrates: CvDemonstratesEdge[];
  expandedGroups: Set<string>;
  focusedEntryId: string;
  activeDropzoneCategory: string | null;
  selectedGroupCategory: string | null;
  onToggleGroup: (category: string) => void;
  onSelectGroup: (category: string) => void;
  onAddEntry: (category: string) => void;
  onToggleExpand: (entryId: string) => void;
  onUpdateCategory: (entryId: string, category: string) => void;
  onToggleEssential: (entryId: string, next: boolean) => void;
  onUpdateDescription: (entryId: string, key: string, text: string) => void;
  onAddDescription: (entryId: string) => void;
  onSelectSkill: (skillId: string) => void;
  onAddSkill: () => void;
  onSelectEntry: (entryId: string) => void;
}

function buildGraphViewNodes(params: BuildParams): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const {
    entries, skills, demonstrates,
    expandedGroups, focusedEntryId, activeDropzoneCategory, selectedGroupCategory,
    onToggleGroup, onSelectGroup, onAddEntry,
    onToggleExpand, onUpdateCategory, onToggleEssential,
    onUpdateDescription, onAddDescription, onSelectSkill, onAddSkill, onSelectEntry,
  } = params;

  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];
  const collapsedProxyParentByChild = new Map<string, string>();

  const relatedRelations = demonstrates.filter(e => e.source === focusedEntryId);
  const relatedSkillIds = new Set(relatedRelations.map(e => e.target));
  const relatedSkills = skills.filter(s => relatedSkillIds.has(s.id));

  const connectedSkillLabels = new Map<string, string[]>();
  const skillById = new Map(skills.map(s => [s.id, s]));
  for (const rel of demonstrates) {
    const skill = skillById.get(rel.target);
    if (!skill) continue;
    const labels = connectedSkillLabels.get(rel.source) ?? [];
    labels.push(skill.label);
    connectedSkillLabels.set(rel.source, labels);
  }

  const categories = orderedCategories(entries);

  categories.forEach((category, idx) => {
    const categoryEntries = entries.filter(e => e.category === category);
    const expanded = expandedGroups.has(category);
    const groupId = `group:${category}`;
    const groupHeight = expanded ? Math.max(160, categoryEntries.length * 84 + 72) : 96;

    const groupData: GroupNodeData = {
      kind: 'group',
      label: displayCategory(category),
      category,
      count: categoryEntries.length,
      countLabel: 'Entries',
      expanded,
      addLabel: 'Add entry',
      isDropzoneActive: activeDropzoneCategory === category,
      onToggleGroup,
      onAddItem: onAddEntry,
      onSelectGroup,
    };

    nodes.push({
      id: groupId,
      type: 'group',
      data: groupData,
      position: { x: idx * 390, y: 30 },
      draggable: false,
      selected: selectedGroupCategory === category,
      style: { width: 340, height: groupHeight },
    } as FlowNode);

    if (!expanded) {
      categoryEntries.forEach(entry => {
        collapsedProxyParentByChild.set(entry.id, groupId);
      });
      return;
    }

    categoryEntries.forEach((entry, entryIndex) => {
      const entryData: EntryNodeData = {
        kind: 'entry',
        label: entryLabel(entry),
        category: entry.category,
        essential: entry.essential,
        descriptions: entry.descriptions,
        expanded: focusedEntryId === entry.id,
        connectedSkillLabels: connectedSkillLabels.get(entry.id) ?? [],
        onSelect: onSelectEntry,
        onToggleExpand,
        onUpdateCategory,
        onToggleEssential,
        onUpdateDescription,
        onAddDescription,
      };

      nodes.push({
        id: entry.id,
        type: 'entry',
        data: entryData,
        parentId: groupId,
        extent: 'parent',
        position: { x: 14, y: 50 + entryIndex * 78 },
        draggable: true,
        style: {
          width: ENTRY_NODE_WIDTH,
          height: ENTRY_NODE_HEIGHT,
          zIndex: focusedEntryId === entry.id ? 30 : 1,
        },
      } as FlowNode);
    });
  });

  const skillsStartX = categories.length * 390;

  if (focusedEntryId) {
    const relatedGroupId = 'group:skills';
    const relatedExpanded = expandedGroups.has('skills');
    const relatedHeight = Math.max(160, relatedSkills.length * 62 + 72);

    nodes.push({
      id: relatedGroupId,
      type: 'group',
      data: {
        kind: 'group',
        label: 'Skills',
        category: 'skills',
        count: relatedSkills.length,
        countLabel: 'Skills',
        expanded: relatedExpanded,
        addLabel: 'Add skill',
        isDropzoneActive: false,
        onToggleGroup,
        onAddItem: () => onAddSkill(),
        onSelectGroup,
      } satisfies GroupNodeData,
      position: { x: skillsStartX + 30, y: 30 },
      draggable: false,
      style: { width: 360, height: relatedHeight },
    } as FlowNode);

    relatedSkills.forEach((skill, index) => {
      if (!relatedExpanded) {
        collapsedProxyParentByChild.set(skill.id, relatedGroupId);
        return;
      }
      const mastery = resolveMasteryLevel(skill.level, toSkillMeta(skill.meta));
      const skillData: SkillNodeData = {
        kind: 'skill',
        label: skill.label,
        category: skill.category,
        essential: skill.essential,
        fillColor: masteryColorForCategory(skill.category, mastery.tag),
        masteryTag: mastery.tag,
        masteryLabel: mastery.label,
        masteryValue: mastery.value,
        masteryIntensity: mastery.intensity,
        related: true,
        shape: 'circle',
        onSelectSkill,
      };
      nodes.push({
        id: skill.id,
        type: 'skill',
        data: skillData,
        parentId: relatedGroupId,
        extent: 'parent',
        position: { x: 14, y: 50 + index * 58 },
        draggable: true,
        style: { width: 320, height: 42 },
      } as FlowNode);
    });

    const renderedEdgeKeys = new Set<string>();
    relatedRelations.forEach(relation => {
      const renderedSource = collapsedProxyParentByChild.get(relation.source) ?? relation.source;
      const renderedTarget = collapsedProxyParentByChild.get(relation.target) ?? relation.target;
      const isProxy = renderedSource !== relation.source || renderedTarget !== relation.target;
      const renderedKey = `${renderedSource}::${renderedTarget}`;
      if (renderedEdgeKeys.has(renderedKey)) return;
      renderedEdgeKeys.add(renderedKey);
      edges.push({
        id: relation.id,
        type: 'proxy',
        source: renderedSource,
        target: renderedTarget,
        label: 'demonstrates',
        data: {
          relation: 'demonstrates',
          realSource: relation.source,
          realTarget: relation.target,
          proxy: isProxy,
        },
        animated: true,
        style: isProxy
          ? { stroke: '#0f766e', strokeWidth: 1.8, strokeDasharray: '6 4', opacity: 0.72 }
          : { stroke: '#0f766e', strokeWidth: 1.8 },
      } as FlowEdge);
    });
  } else {
    const skillsExpanded = expandedGroups.has('skills');
    const skillGroupId = 'group:skills';
    const skillGroupHeight = skillsExpanded ? Math.max(200, skills.length * 62 + 72) : 96;

    nodes.push({
      id: skillGroupId,
      type: 'group',
      data: {
        kind: 'group',
        label: 'Skills',
        category: 'skills',
        count: skills.length,
        countLabel: 'Skills',
        expanded: skillsExpanded,
        addLabel: 'Add skill',
        isDropzoneActive: false,
        onToggleGroup,
        onAddItem: () => onAddSkill(),
        onSelectGroup,
      } satisfies GroupNodeData,
      position: { x: skillsStartX + 30, y: 30 },
      draggable: false,
      style: { width: 360, height: skillGroupHeight },
    } as FlowNode);

    if (skillsExpanded) {
      skills.forEach((skill, skillIndex) => {
        const mastery = resolveMasteryLevel(skill.level, toSkillMeta(skill.meta));
        nodes.push({
          id: skill.id,
          type: 'skill',
          data: {
            kind: 'skill',
            label: skill.label,
            category: skill.category,
            essential: skill.essential,
            fillColor: masteryColorForCategory(skill.category, mastery.tag),
            masteryTag: mastery.tag,
            masteryLabel: mastery.label,
            masteryValue: mastery.value,
            masteryIntensity: mastery.intensity,
            related: false,
            shape: 'circle',
            onSelectSkill,
          } satisfies SkillNodeData,
          parentId: skillGroupId,
          extent: 'parent',
          position: { x: 14, y: 50 + skillIndex * 58 },
          draggable: true,
          style: { width: 320, height: 54 },
        } as FlowNode);
      });
    }

    if (!skillsExpanded) {
      skills.forEach(skill => {
        collapsedProxyParentByChild.set(skill.id, skillGroupId);
      });
    }
  }

  return { nodes, edges };
}

// ── applyTopLevelDagreLayout ──────────────────────────────────────────────────

function applyTopLevelDagreLayout(
  nodes: FlowNode[],
  entries: CvEntry[],
  focusedEntryId: string,
): FlowNode[] {
  const topLevelGroups = nodes.filter(n => n.type === 'group' && !n.parentId);
  if (topLevelGroups.length <= 1) return nodes;

  const focusedCategory = entries.find(e => e.id === focusedEntryId)?.category ?? null;

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'LR', align: 'UL', ranksep: 78, nodesep: 42, marginx: 30, marginy: 30 });

  topLevelGroups.forEach((node, index) => {
    const style = node.style ?? {};
    const baseWidth = asDimension(style.width, node.id === 'group:skills' ? 360 : 340);
    const baseHeight = asDimension(style.height, 160);
    const expandedPanelWidth = focusedCategory && node.id === `group:${focusedCategory}` ? 280 : 0;
    dagreGraph.setNode(node.id, { width: baseWidth + expandedPanelWidth, height: baseHeight });
    if (index > 0) {
      dagreGraph.setEdge(topLevelGroups[index - 1]!.id, node.id);
    }
  });

  dagre.layout(dagreGraph);

  const layoutById = new Map<string, { x: number; y: number }>();
  topLevelGroups.forEach(node => {
    const layoutNode = dagreGraph.node(node.id);
    if (!layoutNode) return;
    const style = node.style ?? {};
    const width = asDimension(style.width, node.id === 'group:skills' ? 360 : 340);
    const height = asDimension(style.height, 160);
    layoutById.set(node.id, { x: layoutNode.x - width / 2, y: layoutNode.y - height / 2 });
  });

  return nodes.map(node => {
    const layout = layoutById.get(node.id);
    if (!layout) return node;
    return { ...node, position: layout };
  });
}

// ── Component ─────────────────────────────────────────────────────────────────

export function CvGraphCanvas({
  entries, skills, demonstrates,
  expandedGroups, focusedEntryId, selectedNodeId,
  activeDropzoneCategory, selectedGroupCategory,
  onNodeClick, onToggleGroup, onSelectGroup,
  onAddEntry, onAddSkill, onToggleExpand, onUpdateCategory,
  onToggleEssential, onUpdateDescription, onAddDescription,
  onSelectSkill, onConnect,
}: Props) {
  const onSelectEntry = useCallback((id: string) => onNodeClick(id, 'entry'), [onNodeClick]);

  const { nodes: rawNodes, edges: rawEdges } = useMemo(() => buildGraphViewNodes({
    entries, skills, demonstrates,
    expandedGroups, focusedEntryId, activeDropzoneCategory, selectedGroupCategory,
    onToggleGroup, onSelectGroup, onAddEntry,
    onToggleExpand, onUpdateCategory, onToggleEssential,
    onUpdateDescription, onAddDescription, onSelectSkill, onAddSkill,
    onSelectEntry,
  }), [
    entries, skills, demonstrates,
    expandedGroups, focusedEntryId, activeDropzoneCategory, selectedGroupCategory,
    onToggleGroup, onSelectGroup, onAddEntry,
    onToggleExpand, onUpdateCategory, onToggleEssential,
    onUpdateDescription, onAddDescription, onSelectSkill, onAddSkill,
    onSelectEntry,
  ]);

  const laidOutNodes = useMemo(
    () => applyTopLevelDagreLayout(rawNodes, entries, focusedEntryId),
    [rawNodes, entries, focusedEntryId]
  );

  // Sync selection state into node data
  const finalNodes = useMemo(() =>
    laidOutNodes.map(n => ({
      ...n,
      selected: n.id === selectedNodeId || n.selected,
    })),
    [laidOutNodes, selectedNodeId]
  );

  const [nodes, , onNodesChange] = useNodesState(finalNodes);
  const [edges, , onEdgesChange] = useEdgesState(rawEdges);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const data = node.data as { kind?: string };
    const kind = data.kind;
    if (kind === 'entry') onNodeClick(node.id, 'entry');
    else if (kind === 'skill') onNodeClick(node.id, 'skill');
    else if (kind === 'group') onNodeClick(node.id, 'group');
    else onNodeClick(node.id, 'entry');
  }, [onNodeClick]);

  const handleConnect = useCallback((connection: Connection) => {
    const source = connection.source ?? '';
    const target = connection.target ?? '';
    // entry -> skill or skill -> entry
    if (source.startsWith('entry:') && target.startsWith('skill:')) {
      onConnect(source, target);
    } else if (source.startsWith('skill:') && target.startsWith('entry:')) {
      onConnect(target, source);
    }
  }, [onConnect]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onNodeClick={handleNodeClick}
      onConnect={handleConnect}
      fitView
      className="bg-background"
    >
      <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="rgba(0,242,255,0.05)" />
      <Controls className="!bg-surface-container !border-outline/20 !shadow-none" />
      <MiniMap className="!bg-surface-container !border-outline/20" />
    </ReactFlow>
  );
}
