import { useCallback, useEffect, useRef } from 'react';

import { useGraphStore } from '@/stores/graph-store';

import { createElkWorker } from './create-elk-worker';

export interface LayoutOptions {
  direction?: 'LR' | 'TB' | 'RL' | 'BT';
  nodeSpacing?: number;
  rankSpacing?: number;
}

type LayoutResult = Array<{ id: string; position: { x: number; y: number } }>;

interface LayoutWorkerRequest {
  type: 'layout';
  requestId: string;
  payload: {
    nodes: Array<{ id: string; width?: number; height?: number }>;
    edges: Array<{ id: string; source: string; target: string }>;
    options: LayoutOptions;
  };
}

interface LayoutWorkerResultResponse {
  type: 'result';
  requestId: string;
  payload: LayoutResult;
}

interface LayoutWorkerErrorResponse {
  type: 'error';
  requestId: string;
  error: string;
}

type LayoutWorkerResponse = LayoutWorkerResultResponse | LayoutWorkerErrorResponse;

type UpdateNode = (
  id: string,
  updates: { position: { x: number; y: number } },
  options: { isVisualOnly: true },
) => void;

export function applyLayoutWorkerResponse(
  response: LayoutWorkerResponse,
  requestId: string,
  updateNode: UpdateNode,
): LayoutResult | null {
  if (response.requestId !== requestId) {
    return null;
  }

  if (response.type === 'error') {
    return [];
  }

  response.payload.forEach(({ id, position }) => {
    updateNode(id, { position }, { isVisualOnly: true });
  });

  return response.payload;
}

export interface UseGraphLayoutResult {
  layout: (options?: LayoutOptions) => Promise<LayoutResult>;
}

export function useGraphLayout(): UseGraphLayoutResult {
  const nodes = useGraphStore((state) => state.nodes);
  const edges = useGraphStore((state) => state.edges);
  const updateNode = useGraphStore((state) => state.updateNode);
  const workerRef = useRef<Worker | null>(null);
  const requestCounterRef = useRef(0);

  useEffect(() => {
    workerRef.current = createElkWorker();
    return () => {
      workerRef.current?.terminate();
      workerRef.current = null;
    };
  }, []);

  const layout = useCallback(
    (options: LayoutOptions = {}): Promise<LayoutResult> => {
      return new Promise((resolve) => {
        if (!workerRef.current) {
          resolve([]);
          return;
        }

        const request: LayoutWorkerRequest = {
          type: 'layout',
          requestId: `layout-${++requestCounterRef.current}`,
          payload: {
            nodes: nodes.map((node) => ({ id: node.id })),
            edges: edges.map((edge) => ({
              id: edge.id,
              source: edge.source,
              target: edge.target,
            })),
            options,
          },
        };

        const handleMessage = (event: MessageEvent<LayoutWorkerResponse>) => {
          const updates = applyLayoutWorkerResponse(event.data, request.requestId, updateNode);
          if (updates === null) {
            return;
          }

          workerRef.current?.removeEventListener('message', handleMessage);
          workerRef.current?.removeEventListener('error', handleError);
          resolve(updates);
        };

        const handleError = () => {
          workerRef.current?.removeEventListener('message', handleMessage);
          workerRef.current?.removeEventListener('error', handleError);
          resolve([]);
        };

        workerRef.current.addEventListener('message', handleMessage);
        workerRef.current.addEventListener('error', handleError);
        workerRef.current.postMessage(request);
      });
    },
    [edges, nodes, updateNode],
  );

  return { layout };
}
