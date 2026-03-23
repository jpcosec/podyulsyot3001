import type { CvProfileGraphPayload, CvEntry, CvSkill } from '../../../types/api.types';
import type { SimpleNode, SimpleEdge } from '../../../pages/global/KnowledgeGraph';

function entryNodeId(id: string) { return `entry:${id}`; }
function skillNodeId(id: string) { return `skill:${id}`; }
function sectionNodeId(cat: string) { return `section:${cat}`; }

const DOC_ID = 'doc:root';
const GROUP_WIDTH = 440;
const SECTION_PADDING = 20;
const SECTION_HEADER = 40;
const ITEM_HEIGHT = 72;
const ITEM_PADDING = 8;
const SECTION_GAP = 16;
const SKILL_X = 600;
const SKILL_HEIGHT = 56;

export function cvProfileToGraph(data: CvProfileGraphPayload): { nodes: SimpleNode[]; edges: SimpleEdge[] } {
  const nodes: SimpleNode[] = [];
  const edges: SimpleEdge[] = [];

  // Group entries by category
  const byCategory = new Map<string, CvEntry[]>();
  for (const entry of data.entries) {
    const arr = byCategory.get(entry.category) ?? [];
    arr.push(entry);
    byCategory.set(entry.category, arr);
  }

  // Build sections and entries
  let sectionY = 0;
  const categories = Array.from(byCategory.keys());

  for (const cat of categories) {
    const catEntries = byCategory.get(cat)!;
    const secId = sectionNodeId(cat);
    const sectionHeight = SECTION_HEADER + catEntries.length * ITEM_HEIGHT + ITEM_PADDING;

    nodes.push({
      id: secId,
      type: 'group',
      parentId: DOC_ID,
      extent: 'parent',
      position: { x: SECTION_PADDING, y: 60 + sectionY },
      style: { width: GROUP_WIDTH - SECTION_PADDING * 2, height: sectionHeight },
      data: { name: cat, category: 'section', properties: {} },
    });

    sectionY += sectionHeight + SECTION_GAP;

    for (let ei = 0; ei < catEntries.length; ei++) {
      const entry = catEntries[ei]!;
      const eId = entryNodeId(entry.id);
      const title = String((entry.fields as Record<string, unknown>)['title'] ?? entry.id);
      const date = String(
        (entry.fields as Record<string, unknown>)['date'] ??
        (entry.fields as Record<string, unknown>)['start_date'] ??
        '',
      );
      nodes.push({
        id: eId,
        type: 'simple',
        parentId: secId,
        extent: 'parent',
        position: { x: ITEM_PADDING, y: SECTION_HEADER + ei * ITEM_HEIGHT },
        data: {
          name: title,
          category: 'entry',
          properties: { date },
          meta: {
            originalId: entry.id,
            fields: entry.fields,
            descriptions: entry.descriptions,
            essential: entry.essential,
          },
        },
      });
    }
  }

  // Document root group — height fits all sections
  const docHeight = 80 + sectionY;
  nodes.unshift({
    id: DOC_ID,
    type: 'group',
    position: { x: 0, y: 0 },
    style: { width: GROUP_WIDTH, height: docHeight },
    data: { name: 'My CV', category: 'document', properties: {} },
  });

  // Skill nodes (right column)
  for (let si = 0; si < data.skills.length; si++) {
    const skill = data.skills[si]!;
    nodes.push({
      id: skillNodeId(skill.id),
      type: 'simple',
      position: { x: SKILL_X, y: si * (SKILL_HEIGHT + 8) },
      data: {
        name: skill.label,
        category: 'skill',
        properties: { level: skill.level ?? '', category: skill.category },
        meta: {
          originalId: skill.id,
          essential: skill.essential,
          skillMeta: skill.meta,
        },
      },
    });
  }

  // Demonstrates edges
  for (const d of data.demonstrates) {
    edges.push({
      id: `demonstrates:${d.id}`,
      source: entryNodeId(d.source),
      target: skillNodeId(d.target),
      type: 'subflow',
      data: { relationType: 'demonstrates', properties: {} },
    });
  }

  return { nodes, edges };
}

interface EntryMeta {
  originalId?: string;
  fields?: Record<string, unknown>;
  descriptions?: CvEntry['descriptions'];
  essential?: boolean;
}

interface SkillMeta {
  originalId?: string;
  essential?: boolean;
  skillMeta?: Record<string, unknown>;
}

export function graphToCvProfile(
  nodes: SimpleNode[],
  edges: SimpleEdge[],
  original: CvProfileGraphPayload,
): CvProfileGraphPayload {
  // Resolve section id → category name
  const sectionCategory = new Map<string, string>();
  for (const n of nodes) {
    if (n.data.category === 'section') {
      sectionCategory.set(n.id, n.data.name);
    }
  }

  const entries: CvEntry[] = nodes
    .filter(n => n.data.category === 'entry')
    .map(n => {
      const meta = n.data.meta as EntryMeta | undefined;
      const parentCat = n.parentId ? (sectionCategory.get(n.parentId) ?? 'general') : 'general';
      return {
        id: meta?.originalId ?? n.id.replace('entry:', ''),
        category: parentCat,
        essential: meta?.essential ?? false,
        fields: meta?.fields ?? { title: n.data.name },
        descriptions: meta?.descriptions ?? [],
      };
    });

  const skills: CvSkill[] = nodes
    .filter(n => n.data.category === 'skill')
    .map(n => {
      const meta = n.data.meta as SkillMeta | undefined;
      return {
        id: meta?.originalId ?? n.id.replace('skill:', ''),
        label: n.data.name,
        category: n.data.properties['category'] ?? 'general',
        essential: meta?.essential ?? false,
        level: n.data.properties['level'] || null,
        meta: meta?.skillMeta ?? {},
      };
    });

  const demonstrates = edges
    .filter(e => e.data?.relationType === 'demonstrates')
    .map(e => ({
      id: e.id.replace('demonstrates:', ''),
      source: e.source.replace('entry:', ''),
      target: e.target.replace('skill:', ''),
      description_keys: [] as string[],
    }));

  return { ...original, entries, skills, demonstrates };
}
