import { useEffect, useMemo, useRef, useState } from 'react';

import { useMutation, useQuery } from '@tanstack/react-query';
import type { ComponentType } from 'react';
import { z } from 'zod';

import { registry } from '@/schema/registry';
import { useGraphStore } from '@/stores/graph-store';

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
      return { nodes: [], edges: [] };
    }

    const ast = schemaToGraph(rawData);
    return { nodes: ast.nodes, edges: ast.edges };
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
      <div className="flex h-screen items-center justify-center">
        <div className="space-y-2">
          <div className="h-12 w-[300px] animate-pulse rounded bg-muted" />
          <div className="h-8 w-[200px] animate-pulse rounded bg-muted" />
          <p className="text-xs text-muted-foreground">Loading schema and graph...</p>
        </div>
      </div>
    );
  }

  if (viewState === 'error') {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center text-destructive">
          <p className="font-medium">Failed to load</p>
          <p className="mt-1 text-sm text-muted-foreground">{String(schemaError || dataError)}</p>
          <button onClick={() => window.location.reload()} className="mt-4 text-sm underline">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <GraphEditor initialNodes={graph.nodes} initialEdges={graph.edges} onSave={handleSave} />;
}
