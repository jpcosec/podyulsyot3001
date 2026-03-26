import { createElement } from 'react';

import { z } from 'zod';

import { registry } from './registry';
import type { NodeTypeDefinition } from './registry.types';

function PlaceholderDot({ colorToken }: { colorToken: string }) {
  return createElement('div', {
    className: 'h-4 w-4 rounded-full',
    style: { backgroundColor: `var(--${colorToken})` },
  });
}

function PlaceholderLabel({ title }: { title: string }) {
  return createElement('span', { className: 'text-xs' }, title);
}

function PlaceholderDetail(props: unknown) {
  const title =
    props && typeof props === 'object' && 'title' in props
      ? String((props as { title: unknown }).title ?? 'Untitled')
      : 'Untitled';

  return createElement(
    'div',
    { className: 'min-w-[150px] rounded border p-2' },
    createElement('p', { className: 'text-xs font-semibold' }, title),
    createElement('p', { className: 'text-[10px] text-muted-foreground' }, 'Placeholder'),
  );
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
      detail: PlaceholderDetail,
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
