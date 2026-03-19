import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  ReactFlow,
  useUpdateNodeInternals,
  type ReactFlowInstance,
  type Connection,
  type Edge,
  type EdgeMouseHandler,
  type EdgeTypes,
  type Node,
  type NodeMouseHandler,
  type NodeTypes,
  type XYPosition,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "@dagrejs/dagre";

import { getCvProfileGraphPayload, saveCvProfileGraphPayload } from "../../api/client";
import { EntryNode } from "../components/cv-graph/EntryNode";
import { GroupNode } from "../components/cv-graph/GroupNode";
import { ProxyEdge } from "../components/cv-graph/ProxyEdge";
import { SkillBallNode } from "../components/cv-graph/SkillBallNode";
import type { EntryNodeData, GroupNodeData, SkillNodeData } from "../components/cv-graph/types";
import {
  MASTERY_SCALE,
  masteryColorForCategory,
  nextDescriptionWeight,
  resolveMasteryLevel,
} from "../lib/mastery-scale";
import type {
  CvDemonstratesEdge,
  CvDescription,
  CvEntry,
  CvProfileGraphPayload,
  CvSkill,
} from "../../types/models";

type FlowNodeData = (EntryNodeData | SkillNodeData | GroupNodeData) & Record<string, unknown>;
type FlowNode = Node<FlowNodeData>;
type FlowEdge = Edge<{
  relation: "demonstrates";
  realSource: string;
  realTarget: string;
  proxy: boolean;
}>;

interface ContainerBounds {
  id: string;
  category: string;
  expanded: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
}

const ENTRY_NODE_WIDTH = 300;
const ENTRY_NODE_HEIGHT = 58;
const ENTRY_ROW_START_Y = 50;
const ENTRY_ROW_GAP = 78;

const ENTRY_CATEGORY_ORDER = [
  "personal_data",
  "contact",
  "legal_status",
  "education",
  "job_experience",
  "internship",
  "publication",
  "project",
  "language_fact",
];

const nodeTypes: NodeTypes = {
  entry: EntryNode,
  skill: SkillBallNode,
  group: GroupNode,
};

const edgeTypes: EdgeTypes = {
  proxy: ProxyEdge,
};

function asText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function displayCategory(value: string): string {
  return value
    .split("_")
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
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

  if (role) {
    return organization ? `${role} @ ${organization}` : role;
  }
  if (degree) {
    return institution ? `${degree} @ ${institution}` : degree;
  }
  if (title) {
    return title;
  }
  if (name) {
    return name;
  }
  if (preferredName) {
    return preferredName;
  }
  if (fullName) {
    return fullName;
  }
  return displayCategory(entry.category);
}

function orderedCategories(entries: CvEntry[]): string[] {
  const discovered = new Set(entries.map((entry) => entry.category));
  const ordered = ENTRY_CATEGORY_ORDER.filter((category) => discovered.has(category));
  for (const category of discovered) {
    if (!ordered.includes(category)) {
      ordered.push(category);
    }
  }
  return ordered;
}

function normalizeDescriptionKey(value: string): string {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return normalized || "description";
}

function isEntryContainerCategory(category: string): boolean {
  return category !== "skills" && category !== "skills_pool" && category !== "related_skills";
}

function categoryFromGroupId(groupId: string): string | null {
  if (!groupId.startsWith("group:")) {
    return null;
  }
  return groupId.slice("group:".length);
}

function clampIndex(value: number, max: number): number {
  if (max <= 0) {
    return 0;
  }
  return Math.min(Math.max(value, 0), max);
}

function reorderCategoryEntries(
  entries: CvEntry[],
  category: string,
  movingEntryId: string,
  targetIndex: number,
  detachedEntries: Record<string, XYPosition>,
): CvEntry[] {
  const orderedIds = entries
    .filter((entry) => entry.category === category)
    .filter((entry) => !detachedEntries[entry.id])
    .map((entry) => entry.id)
    .filter((entryId) => entryId !== movingEntryId);
  const boundedIndex = clampIndex(targetIndex, orderedIds.length);
  orderedIds.splice(boundedIndex, 0, movingEntryId);

  const orderRank = new Map<string, number>(orderedIds.map((id, index) => [id, index]));
  const sortedCategory = entries
    .filter((entry) => entry.category === category)
    .filter((entry) => !detachedEntries[entry.id])
    .slice()
    .sort((left, right) => {
      const leftRank = orderRank.get(left.id) ?? Number.MAX_SAFE_INTEGER;
      const rightRank = orderRank.get(right.id) ?? Number.MAX_SAFE_INTEGER;
      return leftRank - rightRank;
    });
  let cursor = 0;
  return entries.map((entry) => {
    if (entry.category !== category || detachedEntries[entry.id]) {
      return entry;
    }
    const nextEntry = sortedCategory[cursor];
    cursor += 1;
    return nextEntry ?? entry;
  });
}

function resolveNodeAbsolutePosition(node: FlowNode, nodesById: Map<string, FlowNode>): XYPosition {
  if (!node.parentId) {
    return node.position;
  }
  const parent = nodesById.get(node.parentId);
  if (!parent) {
    return node.position;
  }
  const parentAbsolute = resolveNodeAbsolutePosition(parent, nodesById);
  return {
    x: parentAbsolute.x + node.position.x,
    y: parentAbsolute.y + node.position.y,
  };
}

function findContainerAtPoint(
  containers: ContainerBounds[],
  point: XYPosition,
  excludedCategory: string | null,
): ContainerBounds | null {
  return (
    containers.find((container) => {
      if (!container.expanded) {
        return false;
      }
      if (!isEntryContainerCategory(container.category)) {
        return false;
      }
      if (excludedCategory && container.category === excludedCategory) {
        return false;
      }
      return (
        point.x >= container.x &&
        point.x <= container.x + container.width &&
        point.y >= container.y &&
        point.y <= container.y + container.height
      );
    }) ?? null
  );
}

function nodeCenterPoint(node: FlowNode, nodesById: Map<string, FlowNode>): XYPosition {
  const absolute = resolveNodeAbsolutePosition(node, nodesById);
  const style = node.style ?? {};
  const width = asDimension(style.width, ENTRY_NODE_WIDTH);
  const height = asDimension(style.height, ENTRY_NODE_HEIGHT);
  return {
    x: absolute.x + width / 2,
    y: absolute.y + height / 2,
  };
}

function ensureUniqueDescriptionKey(descriptions: CvDescription[]): string {
  const base = normalizeDescriptionKey("new description");
  const used = new Set(descriptions.map((item) => item.key));
  if (!used.has(base)) {
    return base;
  }
  let suffix = 2;
  while (used.has(`${base}_${suffix}`)) {
    suffix += 1;
  }
  return `${base}_${suffix}`;
}

function toSkillMeta(value: Record<string, unknown>): Record<string, unknown> {
  return value;
}

interface BuildGraphParams {
  graph: CvProfileGraphPayload;
  expandedGroups: Set<string>;
  focusedEntryId: string;
  detachedEntries: Record<string, XYPosition>;
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
}

function buildGraphView(params: BuildGraphParams): {
  nodes: FlowNode[];
  edges: FlowEdge[];
  unrelatedSkills: CvSkill[];
  relatedSkills: CvSkill[];
} {
  const {
    graph,
    expandedGroups,
    focusedEntryId,
    detachedEntries,
    activeDropzoneCategory,
    selectedGroupCategory,
    onToggleGroup,
    onSelectGroup,
    onAddEntry,
    onToggleExpand,
    onUpdateCategory,
    onToggleEssential,
    onUpdateDescription,
    onAddDescription,
    onSelectSkill,
    onAddSkill,
  } = params;

  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];
  const collapsedProxyParentByChild = new Map<string, string>();

  const skillById = new Map(graph.skills.map((skill) => [skill.id, skill]));
  const relatedRelations = graph.demonstrates.filter((edge) => edge.source === focusedEntryId);
  const relatedSkillIds = new Set(relatedRelations.map((edge) => edge.target));
  const relatedSkills = graph.skills.filter((skill) => relatedSkillIds.has(skill.id));
  const unrelatedSkills = graph.skills.filter((skill) => !relatedSkillIds.has(skill.id));

  const connectedSkillLabels = new Map<string, string[]>();
  for (const relation of graph.demonstrates) {
    const skill = skillById.get(relation.target);
    if (!skill) {
      continue;
    }
    const labels = connectedSkillLabels.get(relation.source) ?? [];
    labels.push(skill.label);
    connectedSkillLabels.set(relation.source, labels);
  }

  const categories = orderedCategories(graph.entries);

  categories.forEach((category, idx) => {
    const categoryEntries = graph.entries.filter((entry) => entry.category === category);
    const attachedCategoryEntries = categoryEntries.filter((entry) => !detachedEntries[entry.id]);
    const expanded = expandedGroups.has(category);
    const groupId = `group:${category}`;
    const groupHeight = expanded ? Math.max(160, attachedCategoryEntries.length * 84 + 72) : 96;

    const groupData: GroupNodeData = {
      kind: "group",
      label: displayCategory(category),
      category,
      count: attachedCategoryEntries.length,
      countLabel: "Entries",
      expanded,
      addLabel: "Add entry",
      isDropzoneActive: activeDropzoneCategory === category,
      onToggleGroup,
      onAddItem: onAddEntry,
      onSelectGroup,
    };

    nodes.push({
      id: groupId,
      type: "group",
      data: groupData,
      position: { x: idx * 390, y: 30 },
      draggable: false,
      selected: selectedGroupCategory === category,
      style: {
        width: 340,
        height: groupHeight,
      },
    });

    if (!expanded) {
      attachedCategoryEntries.forEach((entry) => {
        collapsedProxyParentByChild.set(entry.id, groupId);
      });
      return;
    }

    attachedCategoryEntries.forEach((entry, entryIndex) => {
      const entryData: EntryNodeData = {
        kind: "entry",
        label: entryLabel(entry),
        category: entry.category,
        essential: entry.essential,
        descriptions: entry.descriptions,
        expanded: focusedEntryId === entry.id,
        connectedSkillLabels: connectedSkillLabels.get(entry.id) ?? [],
        onToggleExpand,
        onUpdateCategory,
        onToggleEssential,
        onUpdateDescription,
        onAddDescription,
      };

      nodes.push({
        id: entry.id,
        type: "entry",
        data: entryData,
        parentId: groupId,
        position: { x: 14, y: 50 + entryIndex * 78 },
        draggable: true,
        style: {
          width: ENTRY_NODE_WIDTH,
          height: ENTRY_NODE_HEIGHT,
          zIndex: focusedEntryId === entry.id ? 30 : 1,
        },
      });
    });
  });

  graph.entries
    .filter((entry) => detachedEntries[entry.id])
    .forEach((entry) => {
      const entryData: EntryNodeData = {
        kind: "entry",
        label: entryLabel(entry),
        category: entry.category,
        essential: entry.essential,
        descriptions: entry.descriptions,
        expanded: focusedEntryId === entry.id,
        connectedSkillLabels: connectedSkillLabels.get(entry.id) ?? [],
        onToggleExpand,
        onUpdateCategory,
        onToggleEssential,
        onUpdateDescription,
        onAddDescription,
      };
      nodes.push({
        id: entry.id,
        type: "entry",
        data: entryData,
        position: detachedEntries[entry.id],
        draggable: true,
        style: {
          width: ENTRY_NODE_WIDTH,
          height: ENTRY_NODE_HEIGHT,
          zIndex: focusedEntryId === entry.id ? 32 : 2,
        },
      });
    });

  const skillsStartX = categories.length * 390;

  if (focusedEntryId) {
    const relatedGroupId = "group:related_skills";
    const relatedExpanded = expandedGroups.has("related_skills");
    const relatedHeight = Math.max(160, relatedSkills.length * 76 + 72);
    nodes.push({
      id: relatedGroupId,
      type: "group",
      data: {
        kind: "group",
        label: "Related Skills",
        category: "related_skills",
        count: relatedSkills.length,
        countLabel: "Skills",
        expanded: relatedExpanded,
        addLabel: "Add skill",
        isDropzoneActive: false,
        onToggleGroup,
        onAddItem: () => {
          onAddSkill();
        },
        onSelectGroup,
      } satisfies GroupNodeData,
      position: { x: skillsStartX + 30, y: 30 },
      draggable: false,
      style: {
        width: 360,
        height: relatedHeight,
      },
    });

    relatedSkills.forEach((skill, index) => {
      if (!relatedExpanded) {
        collapsedProxyParentByChild.set(skill.id, relatedGroupId);
        return;
      }
      const mastery = resolveMasteryLevel(skill.level, toSkillMeta(skill.meta));
      const skillData: SkillNodeData = {
        kind: "skill",
        label: skill.label,
        category: skill.category,
        essential: skill.essential,
        fillColor: masteryColorForCategory(skill.category, mastery.tag),
        masteryTag: mastery.tag,
        masteryLabel: mastery.label,
        masteryValue: mastery.value,
        masteryIntensity: mastery.intensity,
        related: true,
        shape: "circle",
        onSelectSkill,
      };
      nodes.push({
        id: skill.id,
        type: "skill",
        data: skillData,
        parentId: relatedGroupId,
        extent: "parent",
        position: { x: 16, y: 50 + index * 76 },
        draggable: true,
        style: {
          width: 320,
          height: 68,
        },
      });
    });

    const poolGroupId = "group:skills_pool";
    const poolExpanded = expandedGroups.has("skills_pool");
    const poolHeight = Math.max(160, unrelatedSkills.length * 76 + 72);
    nodes.push({
      id: poolGroupId,
      type: "group",
      data: {
        kind: "group",
        label: "Skill Pool",
        category: "skills_pool",
        count: unrelatedSkills.length,
        countLabel: "Skills",
        expanded: poolExpanded,
        addLabel: "Add skill",
        isDropzoneActive: false,
        onToggleGroup,
        onAddItem: () => {
          onAddSkill();
        },
        onSelectGroup,
      } satisfies GroupNodeData,
      position: { x: skillsStartX + 430, y: 30 },
      draggable: false,
      style: {
        width: 360,
        height: poolHeight,
      },
    });

    unrelatedSkills.forEach((skill, index) => {
      if (!poolExpanded) {
        collapsedProxyParentByChild.set(skill.id, poolGroupId);
        return;
      }
      const mastery = resolveMasteryLevel(skill.level, toSkillMeta(skill.meta));
      nodes.push({
        id: skill.id,
        type: "skill",
        data: {
          kind: "skill",
          label: skill.label,
          category: skill.category,
          essential: skill.essential,
          fillColor: masteryColorForCategory(skill.category, mastery.tag),
          masteryTag: mastery.tag,
          masteryLabel: mastery.label,
          masteryValue: mastery.value,
          masteryIntensity: mastery.intensity,
          related: false,
          shape: "circle",
          onSelectSkill,
        } satisfies SkillNodeData,
        parentId: poolGroupId,
        extent: "parent",
        position: { x: 16, y: 50 + index * 76 },
        draggable: true,
        style: {
          width: 320,
          height: 68,
        },
      });
    });

    const renderedEdgeKeys = new Set<string>();
    relatedRelations.forEach((relation) => {
      const renderedSource = collapsedProxyParentByChild.get(relation.source) ?? relation.source;
      const renderedTarget = collapsedProxyParentByChild.get(relation.target) ?? relation.target;
      const isProxy = renderedSource !== relation.source || renderedTarget !== relation.target;
      const renderedKey = `${renderedSource}::${renderedTarget}`;
      if (renderedEdgeKeys.has(renderedKey)) {
        return;
      }
      renderedEdgeKeys.add(renderedKey);
      edges.push({
        id: relation.id,
        type: "proxy",
        source: renderedSource,
        target: renderedTarget,
        label: "demonstrates",
        data: {
          relation: "demonstrates",
          realSource: relation.source,
          realTarget: relation.target,
          proxy: isProxy,
        },
        animated: true,
        style: isProxy
          ? { stroke: "#0f766e", strokeWidth: 1.8, strokeDasharray: "6 4", opacity: 0.72 }
          : { stroke: "#0f766e", strokeWidth: 1.8 },
      });
    });
  } else {
    const skillsExpanded = expandedGroups.has("skills");
    const skillGroupId = "group:skills";
    const skillGroupHeight = skillsExpanded ? Math.max(200, graph.skills.length * 62 + 72) : 96;
    nodes.push({
      id: skillGroupId,
      type: "group",
      data: {
        kind: "group",
        label: "Skills",
        category: "skills",
        count: graph.skills.length,
        countLabel: "Skills",
        expanded: skillsExpanded,
        addLabel: "Add skill",
        isDropzoneActive: false,
        onToggleGroup,
        onAddItem: () => {
          onAddSkill();
        },
        onSelectGroup,
      } satisfies GroupNodeData,
      position: { x: skillsStartX + 30, y: 30 },
      draggable: false,
      style: {
        width: 360,
        height: skillGroupHeight,
      },
    });

    if (skillsExpanded) {
      graph.skills.forEach((skill, skillIndex) => {
        const mastery = resolveMasteryLevel(skill.level, toSkillMeta(skill.meta));
        nodes.push({
          id: skill.id,
          type: "skill",
          data: {
            kind: "skill",
            label: skill.label,
            category: skill.category,
            essential: skill.essential,
            fillColor: masteryColorForCategory(skill.category, mastery.tag),
            masteryTag: mastery.tag,
            masteryLabel: mastery.label,
            masteryValue: mastery.value,
            masteryIntensity: mastery.intensity,
            related: false,
            shape: "circle",
            onSelectSkill,
          } satisfies SkillNodeData,
          parentId: skillGroupId,
          extent: "parent",
          position: { x: 14, y: 50 + skillIndex * 58 },
          draggable: true,
          style: {
            width: 320,
            height: 54,
          },
        });
      });
    }
    if (!skillsExpanded) {
      graph.skills.forEach((skill) => {
        collapsedProxyParentByChild.set(skill.id, skillGroupId);
      });
    }
  }

  return {
    nodes,
    edges,
    unrelatedSkills,
    relatedSkills,
  };
}

function asDimension(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function applyTopLevelDagreLayout(
  nodes: FlowNode[],
  graph: CvProfileGraphPayload | null,
  focusedEntryId: string,
): FlowNode[] {
  const topLevelGroups = nodes.filter((node) => node.type === "group" && !node.parentId);
  if (topLevelGroups.length <= 1) {
    return nodes;
  }

  const focusedCategory = graph?.entries.find((entry) => entry.id === focusedEntryId)?.category ?? null;

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: "LR",
    align: "UL",
    ranksep: 78,
    nodesep: 42,
    marginx: 30,
    marginy: 30,
  });

  topLevelGroups.forEach((node, index) => {
    const style = node.style ?? {};
    const baseWidth = asDimension(style.width, node.id === "group:related_skills" ? 360 : 340);
    const baseHeight = asDimension(style.height, 160);
    const expandedPanelWidth = focusedCategory && node.id === `group:${focusedCategory}` ? 280 : 0;
    const widthForLayout = baseWidth + expandedPanelWidth;
    dagreGraph.setNode(node.id, { width: widthForLayout, height: baseHeight });
    if (index > 0) {
      dagreGraph.setEdge(topLevelGroups[index - 1]?.id, node.id);
    }
  });

  dagre.layout(dagreGraph);

  const layoutById = new Map<string, { x: number; y: number }>();
  topLevelGroups.forEach((node) => {
    const layoutNode = dagreGraph.node(node.id);
    if (!layoutNode) {
      return;
    }
    const style = node.style ?? {};
    const width = asDimension(style.width, node.id === "group:related_skills" ? 360 : 340);
    const height = asDimension(style.height, 160);
    layoutById.set(node.id, {
      x: layoutNode.x - width / 2,
      y: layoutNode.y - height / 2,
    });
  });

  return nodes.map((node) => {
    const layout = layoutById.get(node.id);
    if (!layout) {
      return node;
    }
    return {
      ...node,
      position: layout,
    };
  });
}

function updateEntry(entry: CvEntry, patch: Partial<CvEntry>): CvEntry {
  return {
    ...entry,
    ...patch,
  };
}

function isEntryNodeId(value: string): boolean {
  return value.startsWith("entry:");
}

function isSkillNodeId(value: string): boolean {
  return value.startsWith("skill:");
}

function resolveConnectionPair(
  source: string,
  target: string,
): { entryNodeId: string; skillNodeId: string } | null {
  if (isEntryNodeId(source) && isSkillNodeId(target)) {
    return { entryNodeId: source, skillNodeId: target };
  }
  if (isSkillNodeId(source) && isEntryNodeId(target)) {
    return { entryNodeId: target, skillNodeId: source };
  }
  return null;
}

function CvGraphEditorInner(): JSX.Element {
  const { entryId } = useParams<{ entryId?: string }>();
  const [graph, setGraph] = useState<CvProfileGraphPayload | null>(null);
  const [error, setError] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => new Set());
  const [focusedEntryId, setFocusedEntryId] = useState("");
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [selectedGroupCategory, setSelectedGroupCategory] = useState<string | null>(null);
  const [detachedEntries, setDetachedEntries] = useState<Record<string, XYPosition>>({});
  const [activeDropzoneCategory, setActiveDropzoneCategory] = useState<string | null>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance<
    FlowNode,
    FlowEdge
  > | null>(null);
  const updateNodeInternals = useUpdateNodeInternals();

  const mutateGraph = useCallback(
    (updater: (previous: CvProfileGraphPayload | null) => CvProfileGraphPayload | null) => {
      setGraph(updater);
      setDirty(true);
      setSaveStatus("idle");
    },
    [],
  );

  const handleSave = useCallback(() => {
    if (!graph || saving) {
      return;
    }
    setSaving(true);
    setSaveStatus("idle");
    saveCvProfileGraphPayload(graph)
      .then(() => {
        setDirty(false);
        setSaveStatus("saved");
      })
      .catch((err: Error) => {
        setError(`Save failed: ${err.message}`);
        setSaveStatus("error");
      })
      .finally(() => {
        setSaving(false);
      });
  }, [graph, saving]);

  useEffect(() => {
    getCvProfileGraphPayload()
      .then((payload) => {
        setGraph(payload);
        setError("");
        const categories = orderedCategories(payload.entries);
        setExpandedGroups(new Set(categories.slice(0, 2)));
      })
      .catch((err: Error) => {
        setError(err.message);
      });
  }, []);

  useEffect(() => {
    if (!graph || !entryId) {
      return;
    }
    if (graph.entries.some((entry) => entry.id === entryId)) {
      setFocusedEntryId(entryId);
    }
  }, [entryId, graph]);

  useEffect(() => {
    if (!focusedEntryId) {
      return;
    }
    setExpandedGroups((previous) => {
      const next = new Set(previous);
      next.add("related_skills");
      next.add("skills_pool");
      return next;
    });
  }, [focusedEntryId]);

  const onToggleGroup = useCallback((category: string) => {
    setExpandedGroups((previous) => {
      const next = new Set(previous);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
    if (selectedGroupCategory === category) {
      setSelectedGroupCategory(null);
    }
  }, [selectedGroupCategory]);

  const onSelectGroup = useCallback((category: string) => {
    if (!isEntryContainerCategory(category)) {
      setSelectedGroupCategory(null);
      return;
    }
    setSelectedGroupCategory(category);
    setFocusedEntryId("");
    setSelectedSkillId("");
  }, []);

  const onAddEntry = useCallback((category: string) => {
    const id = `entry:${category}:new_${Date.now()}`;
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      const nextEntry: CvEntry = {
        id,
        category,
        essential: false,
        fields: { title: "New entry" },
        descriptions: [
          {
            key: "new_description",
            text: "Add description",
            weight: "headline",
          },
        ],
      };
      return {
        ...previous,
        entries: [...previous.entries, nextEntry],
      };
    });
    setExpandedGroups((previous) => new Set(previous).add(category));
    setFocusedEntryId(id);
  }, []);

  const onToggleExpand = useCallback((entryNodeId: string) => {
    setFocusedEntryId((previous) => (previous === entryNodeId ? "" : entryNodeId));
  }, []);

  const onUpdateCategory = useCallback((entryNodeId: string, category: string) => {
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      return {
        ...previous,
        entries: previous.entries.map((entry) =>
          entry.id === entryNodeId ? updateEntry(entry, { category }) : entry,
        ),
      };
    });
  }, []);

  const onToggleEssential = useCallback((entryNodeId: string, next: boolean) => {
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      return {
        ...previous,
        entries: previous.entries.map((entry) =>
          entry.id === entryNodeId ? updateEntry(entry, { essential: next }) : entry,
        ),
      };
    });
  }, []);

  const onUpdateDescription = useCallback((entryNodeId: string, key: string, text: string) => {
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      return {
        ...previous,
        entries: previous.entries.map((entry) => {
          if (entry.id !== entryNodeId) {
            return entry;
          }
          return {
            ...entry,
            descriptions: entry.descriptions.map((description) =>
              description.key === key ? { ...description, text } : description,
            ),
          };
        }),
      };
    });
  }, []);

  const onAddDescription = useCallback((entryNodeId: string) => {
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      return {
        ...previous,
        entries: previous.entries.map((entry) => {
          if (entry.id !== entryNodeId) {
            return entry;
          }
          const nextIndex = entry.descriptions.length;
          const nextDescription: CvDescription = {
            key: ensureUniqueDescriptionKey(entry.descriptions),
            text: "New description",
            weight: nextDescriptionWeight(nextIndex),
          };
          return {
            ...entry,
            descriptions: [...entry.descriptions, nextDescription],
          };
        }),
      };
    });
  }, []);

  const onSelectSkill = useCallback((skillId: string) => {
    setSelectedSkillId(skillId);
  }, []);

  const onAddSkill = useCallback(() => {
    const newSkillId = `skill:new_${Date.now()}`;
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      const nextSkill: CvSkill = {
        id: newSkillId,
        label: "New Skill",
        category: "uncategorized",
        essential: false,
        level: "beginner",
        meta: {
          mastery_tag: "beginner",
          mastery_value: 2,
        },
      };
      return {
        ...previous,
        skills: [...previous.skills, nextSkill],
      };
    });
    setSelectedSkillId(newSkillId);
  }, []);

  const mapped = useMemo(() => {
    if (!graph) {
      return {
        nodes: [] as FlowNode[],
        edges: [] as FlowEdge[],
        unrelatedSkills: [] as CvSkill[],
        relatedSkills: [] as CvSkill[],
      };
    }
    const built = buildGraphView({
      graph,
      expandedGroups,
      focusedEntryId,
      detachedEntries,
      activeDropzoneCategory,
      selectedGroupCategory,
      onToggleGroup,
      onSelectGroup,
      onAddEntry,
      onToggleExpand,
      onUpdateCategory,
      onToggleEssential,
      onUpdateDescription,
      onAddDescription,
      onSelectSkill,
      onAddSkill,
    });

    return {
      ...built,
      nodes: applyTopLevelDagreLayout(built.nodes, graph, focusedEntryId),
    };
  }, [
    graph,
    expandedGroups,
    focusedEntryId,
    detachedEntries,
    activeDropzoneCategory,
    selectedGroupCategory,
    onToggleGroup,
    onSelectGroup,
    onAddEntry,
    onToggleExpand,
    onUpdateCategory,
    onToggleEssential,
    onUpdateDescription,
    onAddDescription,
    onSelectSkill,
    onAddSkill,
  ]);

  const isLoading = !graph && !error;

  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>(mapped.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(mapped.edges);

  useEffect(() => {
    setNodes(mapped.nodes);
    setEdges(mapped.edges);
  }, [mapped, setEdges, setNodes]);

  useEffect(() => {
    if (!reactFlowInstance || !mapped.nodes.length) {
      return;
    }
    const rafId = window.requestAnimationFrame(() => {
      void reactFlowInstance.fitView({ padding: 0.14, duration: 180 });
    });
    return () => {
      window.cancelAnimationFrame(rafId);
    };
  }, [reactFlowInstance, mapped.nodes.length, focusedEntryId]);

  useEffect(() => {
    if (!mapped.nodes.length) {
      return;
    }
    const refreshTargets = mapped.nodes
      .filter((node) => node.type === "entry" || node.type === "skill")
      .map((node) => node.id);
    const rafId = window.requestAnimationFrame(() => {
      refreshTargets.forEach((nodeId) => updateNodeInternals(nodeId));
    });
    return () => {
      window.cancelAnimationFrame(rafId);
    };
  }, [mapped.nodes, updateNodeInternals]);

  const containerBounds = useMemo<ContainerBounds[]>(() => {
    const nodesById = new Map(nodes.map((node) => [node.id, node]));
    return nodes
      .filter((node) => node.type === "group" && !node.parentId)
      .map((node) => {
        const category = categoryFromGroupId(node.id);
        if (!category) {
          return null;
        }
        const style = node.style ?? {};
        const position = resolveNodeAbsolutePosition(node, nodesById);
        return {
          id: node.id,
          category,
          expanded: expandedGroups.has(category),
          x: position.x,
          y: position.y,
          width: asDimension(style.width, 340),
          height: asDimension(style.height, 160),
        } satisfies ContainerBounds;
      })
      .filter((item): item is ContainerBounds => Boolean(item));
  }, [expandedGroups, nodes]);

  const onNodeDrag: NodeMouseHandler<FlowNode> = useCallback(
    (_event, node) => {
      const nodesById = new Map(nodes.map((item) => [item.id, item]));
      if (node.type !== "entry") {
        if (activeDropzoneCategory !== null) {
          setActiveDropzoneCategory(null);
        }
        return;
      }
      const parentCategory = node.parentId ? categoryFromGroupId(node.parentId) : null;
      const center = nodeCenterPoint(node, nodesById);
      const dropzone = findContainerAtPoint(containerBounds, center, parentCategory);
      const nextCategory = dropzone?.category ?? null;
      if (activeDropzoneCategory !== nextCategory) {
        setActiveDropzoneCategory(nextCategory);
      }
    },
    [activeDropzoneCategory, containerBounds, nodes],
  );

  const onNodeDragStop: NodeMouseHandler<FlowNode> = useCallback(
    (_event, node) => {
      const nodesById = new Map(nodes.map((item) => [item.id, item]));
      if (activeDropzoneCategory !== null) {
        setActiveDropzoneCategory(null);
      }
      if (node.type !== "entry" || !graph) {
        return;
      }
      const entryId = node.id;
      const absolute = resolveNodeAbsolutePosition(node, nodesById);
      const center = nodeCenterPoint(node, nodesById);
      const parentCategory = node.parentId ? categoryFromGroupId(node.parentId) : null;
      const parentBounds = parentCategory
        ? containerBounds.find((container) => container.category === parentCategory) ?? null
        : null;
      const targetContainer = findContainerAtPoint(containerBounds, center, null);

      if (!parentCategory) {
        if (!targetContainer || !isEntryContainerCategory(targetContainer.category)) {
          setDetachedEntries((previous) => ({
            ...previous,
            [entryId]: absolute,
          }));
          return;
        }

        setDetachedEntries((previous) => {
          if (!(entryId in previous)) {
            return previous;
          }
          const next = { ...previous };
          delete next[entryId];
          return next;
        });

        mutateGraph((previous) => {
          if (!previous) {
            return previous;
          }
          const existing = previous.entries.find((entry) => entry.id === entryId);
          if (!existing) {
            return previous;
          }
          const movedEntries = previous.entries.map((entry) =>
            entry.id === entryId ? updateEntry(entry, { category: targetContainer.category }) : entry,
          );
          return {
            ...previous,
            entries: reorderCategoryEntries(
              movedEntries,
              targetContainer.category,
              entryId,
              Number.MAX_SAFE_INTEGER,
              detachedEntries,
            ),
          };
        });
        setExpandedGroups((previous) => new Set(previous).add(targetContainer.category));
        return;
      }

      if (
        parentBounds &&
        absolute.x >= parentBounds.x &&
        absolute.x <= parentBounds.x + parentBounds.width &&
        absolute.y >= parentBounds.y &&
        absolute.y <= parentBounds.y + parentBounds.height
      ) {
        const relativeY = absolute.y - parentBounds.y - ENTRY_ROW_START_Y;
        const targetIndex = Math.round(relativeY / ENTRY_ROW_GAP);
        mutateGraph((previous) => {
          if (!previous) {
            return previous;
          }
          return {
            ...previous,
            entries: reorderCategoryEntries(
              previous.entries,
              parentCategory,
              entryId,
              targetIndex,
              detachedEntries,
            ),
          };
        });
        return;
      }

      if (targetContainer && isEntryContainerCategory(targetContainer.category)) {
        mutateGraph((previous) => {
          if (!previous) {
            return previous;
          }
          const movedEntries = previous.entries.map((entry) =>
            entry.id === entryId ? updateEntry(entry, { category: targetContainer.category }) : entry,
          );
          return {
            ...previous,
            entries: reorderCategoryEntries(
              movedEntries,
              targetContainer.category,
              entryId,
              Number.MAX_SAFE_INTEGER,
              detachedEntries,
            ),
          };
        });
        setExpandedGroups((previous) => new Set(previous).add(targetContainer.category));
        return;
      }

      setDetachedEntries((previous) => ({
        ...previous,
        [entryId]: absolute,
      }));
    },
    [activeDropzoneCategory, containerBounds, detachedEntries, graph, mutateGraph, nodes],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) {
        return;
      }

      const pair = resolveConnectionPair(connection.source, connection.target);
      if (!pair) {
        return;
      }
      const { entryNodeId, skillNodeId } = pair;

      mutateGraph((previous) => {
        if (!previous) {
          return previous;
        }
        const hasEntry = previous.entries.some((item) => item.id === entryNodeId);
        const hasSkill = previous.skills.some((item) => item.id === skillNodeId);
        if (!hasEntry || !hasSkill) {
          return previous;
        }
        if (
          previous.demonstrates.some(
            (item) => item.source === entryNodeId && item.target === skillNodeId,
          )
        ) {
          return previous;
        }
        const entry = previous.entries.find((item) => item.id === entryNodeId);
        if (!entry) {
          return previous;
        }
        const nextEdge: CvDemonstratesEdge = {
          id: `edge:${entryNodeId}:demonstrates:${skillNodeId}`,
          source: entryNodeId,
          target: skillNodeId,
          description_keys: entry.descriptions.map((description) => description.key),
        };
        return {
          ...previous,
          demonstrates: [...previous.demonstrates, nextEdge],
        };
      });
      setFocusedEntryId(entryNodeId);
      setSelectedSkillId(skillNodeId);
    },
    [mutateGraph],
  );

  const onNodeClick: NodeMouseHandler<FlowNode> = useCallback((_event, node) => {
    if (node.data.kind === "entry") {
      setFocusedEntryId((previous) => (previous === node.id ? "" : node.id));
      setSelectedSkillId("");
      setSelectedGroupCategory(null);
      return;
    }
    if (node.data.kind === "skill") {
      setSelectedSkillId(node.id);
      setSelectedGroupCategory(null);
      return;
    }
    if (node.data.kind === "group") {
      const category = categoryFromGroupId(node.id);
      if (!category || !isEntryContainerCategory(category)) {
        setSelectedGroupCategory(null);
        return;
      }
      setSelectedGroupCategory((previous) => (previous === category ? null : category));
      setFocusedEntryId("");
      setSelectedSkillId("");
    }
  }, []);

  const onEdgeClick: EdgeMouseHandler<FlowEdge> = useCallback((_event, edge) => {
    if (edge.data?.relation !== "demonstrates") {
      return;
    }
    setFocusedEntryId(edge.data.realSource ?? edge.source);
    setSelectedSkillId(edge.data.realTarget ?? edge.target);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedGroupCategory(null);
  }, []);

  const focusedEntry = graph?.entries.find((entry) => entry.id === focusedEntryId) ?? null;
  const selectedSkill = graph?.skills.find((skill) => skill.id === selectedSkillId) ?? null;
  const selectedGroupEntries = useMemo(() => {
    if (!graph || !selectedGroupCategory) {
      return [] as CvEntry[];
    }
    return graph.entries.filter(
      (entry) => entry.category === selectedGroupCategory && !detachedEntries[entry.id],
    );
  }, [detachedEntries, graph, selectedGroupCategory]);

  const moveEntryInsideSelectedGroup = useCallback(
    (entryId: string, direction: "up" | "down") => {
      if (!selectedGroupCategory || !graph) {
        return;
      }
      const entriesInGroup = graph.entries.filter((entry) => entry.category === selectedGroupCategory);
      const currentIndex = entriesInGroup.findIndex((entry) => entry.id === entryId);
      if (currentIndex === -1) {
        return;
      }
      const delta = direction === "up" ? -1 : 1;
      const targetIndex = clampIndex(currentIndex + delta, entriesInGroup.length - 1);
      mutateGraph((previous) => {
        if (!previous) {
          return previous;
        }
        return {
          ...previous,
          entries: reorderCategoryEntries(
            previous.entries,
            selectedGroupCategory,
            entryId,
            targetIndex,
            detachedEntries,
          ),
        };
      });
    },
    [detachedEntries, graph, mutateGraph, selectedGroupCategory],
  );

  const removeEntryFromContainer = useCallback(
    (entryId: string) => {
      if (!selectedGroupCategory) {
        return;
      }
      const selectedBounds = containerBounds.find(
        (container) => container.category === selectedGroupCategory,
      );
      const fallbackIndex = selectedGroupEntries.findIndex((entry) => entry.id === entryId);
      const fallbackY = selectedBounds
        ? selectedBounds.y + ENTRY_ROW_START_Y + Math.max(fallbackIndex, 0) * ENTRY_ROW_GAP
        : 120;
      const fallbackX = selectedBounds ? selectedBounds.x + selectedBounds.width + 48 : 140;
      setDetachedEntries((previous) => ({
        ...previous,
        [entryId]: { x: fallbackX, y: fallbackY },
      }));
    },
    [containerBounds, selectedGroupCategory, selectedGroupEntries],
  );

  const updateSelectedSkill = (patch: Partial<CvSkill>) => {
    if (!selectedSkillId) {
      return;
    }
    mutateGraph((previous) => {
      if (!previous) {
        return previous;
      }
      return {
        ...previous,
        skills: previous.skills.map((skill) =>
          skill.id === selectedSkillId
            ? {
                ...skill,
                ...patch,
              }
            : skill,
        ),
      };
    });
  };

  const selectedMastery = selectedSkill
    ? resolveMasteryLevel(selectedSkill.level, toSkillMeta(selectedSkill.meta))
    : null;

  return (
    <section className="panel cv-graph-editor-shell space-y-2">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to="/sandbox">Sandbox</Link>
        <span>/</span>
        <span>CV Graph Editor</span>
      </div>

      <div className="cv-graph-header">
        <div>
          <h1>CV Graph Editor (Entry / Skill)</h1>
          <p>
            Click an entry to expand editing to the right. Match skills by dragging connections
            between entry and skill handles.
          </p>
        </div>
        <div className="cv-graph-save-controls">
          <button
            type="button"
            className={`cv-save-button ${dirty ? "cv-save-button-dirty" : ""}`}
            disabled={!dirty || saving}
            onClick={handleSave}
          >
            {saving ? "Saving..." : dirty ? "Save changes" : "Saved"}
          </button>
          {saveStatus === "saved" ? <span className="cv-save-status cv-save-ok">Saved</span> : null}
          {saveStatus === "error" ? <span className="cv-save-status cv-save-err">Failed</span> : null}
        </div>
      </div>
      {error ? <p className="error">{error}</p> : null}

      <div className="cv-graph-layout">
        <div className="cv-graph-canvas-wrap">
          {isLoading ? (
            <div className="cv-graph-skeleton" role="status" aria-label="Loading CV graph editor">
              <div className="cv-skeleton-title" />
              <div className="cv-skeleton-row">
                <div className="cv-skeleton-card" />
                <div className="cv-skeleton-card" />
                <div className="cv-skeleton-card" />
              </div>
              <div className="cv-skeleton-row cv-skeleton-row-wide">
                <div className="cv-skeleton-card" />
              </div>
            </div>
          ) : (
            <ReactFlow<FlowNode, FlowEdge>
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeDrag={onNodeDrag}
              onNodeDragStop={onNodeDragStop}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              onPaneClick={onPaneClick}
              onInit={setReactFlowInstance}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              minZoom={0.1}
              fitView
              attributionPosition="bottom-left"
            >
              <MiniMap pannable zoomable />
              <Controls />
              <Background gap={18} size={1} />
            </ReactFlow>
          )}
        </div>

        <aside className="cv-graph-sidepanel shadow-sm">
          <h2>Skill Palette</h2>
          <p className="cv-muted">
            {focusedEntry
              ? `Focused entry: ${entryLabel(focusedEntry)}`
              : "Select an entry to split related and unrelated skills."}
          </p>
          {Object.keys(detachedEntries).length ? (
            <p className="cv-muted">
              Detached entries are a sandbox-only layout state and are not persisted by Save.
            </p>
          ) : null}

          <div className="cv-side-box">
            <h3>Unrelated Skills</h3>
            <div className="cv-side-skill-grid">
              {isLoading ? (
                <div className="cv-side-skill-loading" role="status" aria-label="Loading skill palette">
                  <div className="cv-skeleton-chip" />
                  <div className="cv-skeleton-chip" />
                  <div className="cv-skeleton-chip" />
                </div>
              ) : (
                mapped.unrelatedSkills.map((skill) => {
                  const mastery = resolveMasteryLevel(skill.level, toSkillMeta(skill.meta));
                  return (
                    <button
                      key={skill.id}
                      type="button"
                      className={`cv-side-skill-chip ${selectedSkillId === skill.id ? "cv-side-skill-chip-active" : ""}`}
                      style={{
                        borderColor: masteryColorForCategory(skill.category, mastery.tag),
                      }}
                      onClick={() => setSelectedSkillId(skill.id)}
                    >
                      <span>{skill.label}</span>
                      <small>
                        {mastery.label} ({mastery.value}/5)
                      </small>
                    </button>
                  );
                })
              )}
            </div>
            <button type="button" className="cv-plus-button w-full" onClick={onAddSkill}>
              + Add skill
            </button>
          </div>

          {selectedSkill ? (
            <div className="cv-side-box">
              <h3>Selected Skill</h3>
              <label className="cv-inline-field">
                <span>Name</span>
                <input
                  value={selectedSkill.label}
                  onChange={(event) => updateSelectedSkill({ label: event.target.value })}
                />
              </label>

              <label className="cv-inline-field">
                <span>Category</span>
                <input
                  value={selectedSkill.category}
                  onChange={(event) => updateSelectedSkill({ category: event.target.value })}
                />
              </label>

              <label className="cv-inline-field">
                <span>Mastery</span>
                <select
                  value={selectedMastery?.tag ?? "intermediate"}
                  onChange={(event) => {
                    const next = MASTERY_SCALE.find((item) => item.tag === event.target.value);
                    if (!next) {
                      return;
                    }
                    updateSelectedSkill({
                      level: next.label,
                      meta: {
                        ...toSkillMeta(selectedSkill.meta),
                        mastery_tag: next.tag,
                        mastery_value: next.value,
                      },
                    });
                  }}
                >
                  {MASTERY_SCALE.map((item) => (
                    <option key={item.tag} value={item.tag}>
                      {item.label} ({item.value}/5)
                    </option>
                  ))}
                </select>
              </label>

              <label className="cv-inline-checkbox">
                <input
                  type="checkbox"
                  checked={selectedSkill.essential}
                  onChange={(event) => updateSelectedSkill({ essential: event.target.checked })}
                />
                <span>Essential skill</span>
              </label>
            </div>
          ) : null}

          {selectedGroupCategory ? (
            <div className="cv-side-box">
              <h3>Container Elements ({displayCategory(selectedGroupCategory)})</h3>
              {selectedGroupEntries.length ? (
                <div className="cv-container-elements-list">
                  {selectedGroupEntries.map((entry, index) => (
                    <div key={entry.id} className="cv-container-element-item">
                      <span className="cv-container-element-label">{entryLabel(entry)}</span>
                      <div className="cv-container-element-actions">
                        <button
                          type="button"
                          className="cv-order-btn"
                          disabled={index === 0}
                          onClick={() => moveEntryInsideSelectedGroup(entry.id, "up")}
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          className="cv-order-btn"
                          disabled={index === selectedGroupEntries.length - 1}
                          onClick={() => moveEntryInsideSelectedGroup(entry.id, "down")}
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          className="cv-order-btn cv-order-btn-remove"
                          onClick={() => removeEntryFromContainer(entry.id)}
                        >
                          Extract
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="cv-muted">This container has no attached entries.</p>
              )}
            </div>
          ) : null}

          <div className="cv-side-box">
            <h3>Mastery Scale</h3>
            <ul className="cv-mastery-list">
              {MASTERY_SCALE.map((level) => (
                <li key={level.tag}>
                  <strong>{level.label}</strong> ({level.value}/5) - {level.cefrEquiv}
                </li>
              ))}
            </ul>
          </div>

          <div className="cv-graph-meta">
            <h3>Graph Meta</h3>
            <p>
              Entries: <strong>{graph?.entries.length ?? 0}</strong>
            </p>
            <p>
              Skills: <strong>{graph?.skills.length ?? 0}</strong>
            </p>
            <p>
              Related skills: <strong>{mapped.relatedSkills.length}</strong>
            </p>
            <p>
              Demonstrates: <strong>{graph?.demonstrates.length ?? 0}</strong>
            </p>
            <p>
              Snapshot: <strong>{graph?.snapshot_version ?? "-"}</strong>
            </p>
            <p>
              Captured on: <strong>{graph?.captured_on ?? "-"}</strong>
            </p>
          </div>
        </aside>
      </div>
    </section>
  );
}

export function CvGraphEditorPage(): JSX.Element {
  return (
    <ReactFlowProvider>
      <CvGraphEditorInner />
    </ReactFlowProvider>
  );
}
