import { useEffect, useMemo, useRef, useState } from 'react';

import { useMutation, useQuery } from '@tanstack/react-query';
import type { ComponentType } from 'react';
import { z } from 'zod';

import { registry } from '@/schema/registry';
import type { ASTEdge, ASTNode } from '@/stores/types';
import { useGraphStore } from '@/stores/graph-store';

/**
 * GraphEditorPage - L1 Application Layer
 * 
 * Orchestrates the entire graph editor experience:
 * - Fetches schema and graph data from the data provider
 * - Registers node types in the registry at runtime
 * - Translates raw data to AST format for the canvas
 * - Handles save operations (AST -> domain -> provider)
 * 
 * This is the top-level page component. It knows about domain concepts
 * (Jobs, CVs, skills) but knows nothing about ReactFlow.
 * 
 * @example
 * ```tsx
 * <GraphEditorPage />
 * ```
 */

import { GraphEditor } from '../L2-canvas/GraphEditor';
import { graphDataProvider, type GraphSchema } from '../lib/data-provider';
import { graphToDomain } from '../lib/graph-to-domain';
import { schemaToGraph } from '../lib/schema-to-graph';

type RegistryWriter = {
  register: (definition: {
    typeId: string;
    label: string;
    icon: string;
    category: string;
    colorToken: string;
    payloadSchema: z.ZodSchema;
    renderers: {
      dot: ComponentType<{ colorToken: string }>;
      label: ComponentType<{ title: string; icon: string }>;
      detail: ComponentType<unknown>;
    };
    defaultSize: { width: number; height: number };
    allowedConnections: string[];
  }) => void;
};

type GraphEditorPageViewStateArgs = {
  schemaLoading: boolean;
  dataLoading: boolean;
  isSchemaRegistered: boolean;
  schemaError: unknown;
  dataError: unknown;
};

export function getGraphEditorPageViewState(args: GraphEditorPageViewStateArgs): 'error' | 'loading' | 'ready' {
  if (args.schemaError || args.dataError) {
    return 'error';
  }

  if (args.schemaLoading || args.dataLoading || !args.isSchemaRegistered) {
    return 'loading';
  }

  return 'ready';
}

const PlaceholderDot = ({ colorToken }: { colorToken: string }) => (
  <div className="h-4 w-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
);

const PlaceholderLabel = ({ title }: { title: string; icon: string }) => (
  <span className="text-xs">{title}</span>
);

const PlaceholderDetail = (props: unknown) => {
  const title =
    props && typeof props === 'object' && 'title' in props && typeof props.title === 'string'
      ? props.title
      : 'Untitled';

  return (
    <div className="min-w-[150px] rounded border p-2">
      <p className="text-xs font-semibold">{title}</p>
      <p className="text-[10px] text-muted-foreground">Loading...</p>
    </div>
  );
};

function toPayloadSchema(attributes: Record<string, { type: string; required: boolean }>): z.ZodSchema {
  const shape: Record<string, z.ZodTypeAny> = {};

  Object.entries(attributes).forEach(([key, attr]) => {
    const isRequired = Boolean(attr.required);

    if (attr.type === 'number') {
      shape[key] = isRequired ? z.coerce.number() : z.coerce.number().optional();
      return;
    }

    shape[key] = isRequired ? z.string().min(1) : z.string().optional();
  });

  return z.object(shape);
}

export function registerSchemaTypes(schema: GraphSchema, targetRegistry: RegistryWriter = registry): void {
  schema.node_types.forEach((typeDef) => {
    targetRegistry.register({
      typeId: typeDef.id,
      label: typeDef.display_name,
      icon: typeDef.visual?.icon || 'circle',
      category: 'entity',
      colorToken: typeDef.visual?.color_token || `token-${typeDef.id}`,
      payloadSchema: toPayloadSchema(typeDef.attributes || {}),
      renderers: {
        dot: PlaceholderDot,
        label: PlaceholderLabel,
        detail: PlaceholderDetail,
      },
      defaultSize: { width: 180, height: 70 },
      allowedConnections: typeDef.allowed_connections || [],
    });
  });
}

export function GraphEditorPage() {
  const loadGraph = useGraphStore((state) => state.loadGraph);
  const isDirty = useGraphStore((state) => state.isDirty);
  const [isSchemaRegistered, setIsSchemaRegistered] = useState(false);
  const hasHydratedRef = useRef(false);

  const { data: schemaData, isLoading: schemaLoading, error: schemaError } = useQuery({
    queryKey: ['schema'],
    queryFn: () => graphDataProvider.getSchema(),
  });

  const { data: rawData, isLoading: dataLoading, error: dataError } = useQuery({
    queryKey: ['graph'],
    queryFn: () => graphDataProvider.getGraph(),
  });

  useEffect(() => {
    if (!schemaData) {
      setIsSchemaRegistered(false);
      return;
    }

    registerSchemaTypes(schemaData);
    setIsSchemaRegistered(true);
  }, [schemaData]);

  const graph = useMemo(() => {
    if (!rawData || !isSchemaRegistered) {
      return { nodes: [] as ASTNode[], edges: [] as ASTEdge[] };
    }

    // Direct pass-through - no translation layer
    const data = rawData as { nodes: ASTNode[]; edges: ASTEdge[] };
    return { nodes: data.nodes, edges: data.edges };
  }, [rawData, isSchemaRegistered]);

  useEffect(() => {
    if (!rawData || !isSchemaRegistered) {
      return;
    }

    if (!hasHydratedRef.current) {
      hasHydratedRef.current = true;
      loadGraph(graph.nodes, graph.edges);
      return;
    }

    if (isDirty()) {
      return;
    }

    loadGraph(graph.nodes, graph.edges);
  }, [graph.edges, graph.nodes, isSchemaRegistered, loadGraph, rawData, isDirty]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const current = useGraphStore.getState();
      return graphDataProvider.saveGraph(graphToDomain(current.nodes, current.edges));
    },
    onSuccess: () => {
      useGraphStore.getState().markSaved();
    },
  });

  const handleSave = () => {
    if (!isDirty()) {
      return;
    }

    saveMutation.mutate();
  };

  const viewState = getGraphEditorPageViewState({
    schemaLoading,
    dataLoading,
    isSchemaRegistered,
    schemaError,
    dataError,
  });

  if (viewState === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center px-6">
        <div className="glass-panel w-full max-w-xl rounded-[2rem] p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-[0.32em] text-primary">Review Workbench</p>
              <h1 className="mt-2 font-headline text-3xl font-bold text-on-surface">Preparing your graph studio</h1>
            </div>
            <div className="h-14 w-14 animate-pulse rounded-2xl border border-primary/30 bg-primary/10" />
          </div>
          <div className="space-y-3">
            <div className="h-16 animate-pulse rounded-2xl bg-white/5" />
            <div className="grid grid-cols-2 gap-3">
              <div className="h-24 animate-pulse rounded-2xl bg-white/5" />
              <div className="h-24 animate-pulse rounded-2xl bg-white/5" />
            </div>
          </div>
          <p className="mt-5 text-sm text-muted-foreground">Loading schema, graph state, and editor modules...</p>
        </div>
      </div>
    );
  }

  if (viewState === 'error') {
    return (
      <div className="flex h-screen items-center justify-center px-6">
        <div className="glass-panel w-full max-w-lg rounded-[2rem] p-8 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.32em] text-secondary">Connection lost</p>
          <h1 className="mt-3 font-headline text-3xl font-bold text-on-surface">The editor could not boot cleanly</h1>
          <p className="mt-3 text-sm text-muted-foreground">{String(schemaError || dataError)}</p>
          <button onClick={() => window.location.reload()} className="mt-6 rounded-full border border-secondary/30 bg-secondary/10 px-5 py-2 text-sm font-medium text-secondary transition hover:bg-secondary/20">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <GraphEditor initialNodes={graph.nodes} initialEdges={graph.edges} onSave={handleSave} />;
}
