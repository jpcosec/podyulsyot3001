import ELK from 'elkjs/lib/elk.bundled.js';

interface LayoutOptions {
  direction?: 'LR' | 'TB' | 'RL' | 'BT';
  nodeSpacing?: number;
  rankSpacing?: number;
}

interface LayoutRequestMessage {
  type: 'layout';
  requestId: string;
  payload: {
    nodes: Array<{ id: string; width?: number; height?: number }>;
    edges: Array<{ id: string; source: string; target: string }>;
    options?: LayoutOptions;
  };
}

interface LayoutResultResponseMessage {
  type: 'result';
  requestId: string;
  payload: Array<{ id: string; position: { x: number; y: number } }>;
}

interface LayoutErrorResponseMessage {
  type: 'error';
  requestId: string;
  error: string;
}

type LayoutResponseMessage = LayoutResultResponseMessage | LayoutErrorResponseMessage;

const elk = new ELK();

self.onmessage = async (event: MessageEvent<LayoutRequestMessage>) => {
  if (event.data.type !== 'layout') {
    return;
  }

  const { requestId } = event.data;
  const { nodes, edges, options } = event.data.payload;
  const direction = options?.direction ?? 'LR';
  const nodeSpacing = options?.nodeSpacing ?? 50;
  const rankSpacing = options?.rankSpacing ?? 100;

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': direction,
      'elk.spacing.nodeNode': String(nodeSpacing),
      'elk.layered.spacing.nodeNodeBetweenLayers': String(rankSpacing),
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: node.width ?? 170,
      height: node.height ?? 68,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  try {
    const layouted = await elk.layout(graph);

    const response: LayoutResponseMessage = {
      type: 'result',
      requestId,
      payload: (layouted.children ?? [])
        .filter((child): child is typeof child & { x: number; y: number } => {
          return typeof child.x === 'number' && typeof child.y === 'number';
        })
        .map((child) => ({
          id: child.id,
          position: { x: child.x, y: child.y },
        })),
    };

    self.postMessage(response);
  } catch {
    const response: LayoutResponseMessage = {
      type: 'error',
      requestId,
      error: 'Layout computation failed',
    };
    self.postMessage(response);
  }
};

export {};
