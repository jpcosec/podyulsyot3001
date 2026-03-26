import { createElement } from 'react';

import { z } from 'zod';

import { EntityCard } from '@/components/content/EntityCard';
import { PlaceholderNode } from '@/components/content/PlaceholderNode';

import { registry } from './registry';
import type { NodeTypeDefinition } from './registry.types';

function PlaceholderDot({ colorToken }: { colorToken: string }) {
  return createElement(PlaceholderNode, { colorToken });
}

function PlaceholderLabel({ title }: { title: string }) {
  return createElement('span', { className: 'text-xs' }, title);
}

function toEntityCardProps(props: unknown, fallbackCategory: string, fallbackVisualToken: string) {
  const candidate = props && typeof props === 'object' ? (props as Record<string, unknown>) : {};

  const titleCandidate = candidate.title ?? candidate.name;
  const title = typeof titleCandidate === 'string' && titleCandidate.trim().length > 0
    ? titleCandidate
    : 'Untitled';

  const category =
    typeof candidate.category === 'string' && candidate.category.trim().length > 0
      ? candidate.category
      : fallbackCategory;

  const visualToken =
    typeof candidate.visualToken === 'string' && candidate.visualToken.trim().length > 0
      ? candidate.visualToken
      : fallbackVisualToken;

  const badges = Array.isArray(candidate.badges)
    ? candidate.badges.filter((badge): badge is string => typeof badge === 'string')
    : undefined;

  const propertiesSource =
    candidate.properties && typeof candidate.properties === 'object'
      ? (candidate.properties as Record<string, unknown>)
      : {};

  const properties = Object.fromEntries(
    Object.entries(propertiesSource).map(([key, value]) => [key, String(value)]),
  );

  return {
    title,
    category,
    properties,
    badges,
    visualToken,
  };
}

function detailRendererFor(category: string, visualToken: string) {
  return (props: unknown) =>
    createElement(EntityCard, toEntityCardProps(props, category, visualToken));
}

const defaultNodeTypes: NodeTypeDefinition[] = [
  {
    typeId: 'person',
    label: 'Person',
    icon: 'user',
    category: 'entity',
    colorToken: 'token-person',
    payloadSchema: z.object({
      name: z.string().min(1),
      role: z.string().optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Person', 'token-person'),
    },
    defaultSize: { width: 200, height: 80 },
    allowedConnections: ['skill', 'project', 'publication', 'concept'],
  },

  {
    typeId: 'skill',
    label: 'Skill',
    icon: 'wrench',
    category: 'component',
    colorToken: 'token-skill',
    payloadSchema: z.object({
      name: z.string().min(1),
      level: z.enum(['basic', 'intermediate', 'advanced']).optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Skill', 'token-skill'),
    },
    defaultSize: { width: 180, height: 60 },
    allowedConnections: ['person', 'project', 'concept'],
  },

  {
    typeId: 'project',
    label: 'Project',
    icon: 'folder',
    category: 'content',
    colorToken: 'token-project',
    payloadSchema: z.object({
      name: z.string().min(1),
      stage: z.enum(['draft', 'active', 'completed']).optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Project', 'token-project'),
    },
    defaultSize: { width: 200, height: 80 },
    allowedConnections: ['person', 'skill', 'publication'],
  },

  {
    typeId: 'publication',
    label: 'Publication',
    icon: 'file-text',
    category: 'content',
    colorToken: 'token-publication',
    payloadSchema: z.object({
      title: z.string().min(1),
      year: z.string().optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Publication', 'token-publication'),
    },
    defaultSize: { width: 220, height: 80 },
    allowedConnections: ['person', 'project', 'concept'],
  },

  {
    typeId: 'concept',
    label: 'Concept',
    icon: 'lightbulb',
    category: 'entity',
    colorToken: 'token-concept',
    payloadSchema: z.object({
      name: z.string().min(1),
      description: z.string().optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Concept', 'token-concept'),
    },
    defaultSize: { width: 180, height: 60 },
    allowedConnections: ['person', 'skill', 'project', 'publication'],
  },

  {
    typeId: 'document',
    label: 'Document',
    icon: 'file',
    category: 'content',
    colorToken: 'token-document',
    payloadSchema: z.object({
      title: z.string().min(1),
      type: z.enum(['cv', 'resume', 'report', 'other']).optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Document', 'token-document'),
    },
    defaultSize: { width: 200, height: 80 },
    allowedConnections: ['section', 'entry'],
  },

  {
    typeId: 'section',
    label: 'Section',
    icon: 'list',
    category: 'content',
    colorToken: 'token-section',
    payloadSchema: z.object({
      title: z.string().min(1),
      order: z.coerce.number().optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Section', 'token-section'),
    },
    defaultSize: { width: 180, height: 60 },
    allowedConnections: ['document', 'entry'],
  },

  {
    typeId: 'entry',
    label: 'Entry',
    icon: 'list-item',
    category: 'content',
    colorToken: 'token-entry',
    payloadSchema: z.object({
      title: z.string().min(1),
      date: z.string().optional(),
    }),
    renderers: {
      dot: PlaceholderDot,
      label: PlaceholderLabel,
      detail: detailRendererFor('Entry', 'token-entry'),
    },
    defaultSize: { width: 160, height: 50 },
    allowedConnections: ['section'],
  },
];

function registerIfMissing(definition: NodeTypeDefinition): void {
  if (registry.get(definition.typeId)) {
    return;
  }

  registry.register(definition);
}

export function registerDefaultNodeTypes(): void {
  defaultNodeTypes.forEach(registerIfMissing);
}
