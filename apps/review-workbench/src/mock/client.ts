import graphData from './fixtures/graph_data.json';
import { validateGraphData, graphPayloadSchema } from '@/schema/graph-validation';

const delay = <T>(v: T, ms = 80): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), ms));

export interface GraphPayload {
  nodes: unknown[];
  edges: unknown[];
}

export const mockClient = {
  async getGraph(): Promise<GraphPayload> {
    const validation = validateGraphData(graphData);
    
    if (!validation.success || !validation.data) {
      console.error('Graph data validation errors:', validation.errors);
      throw new Error(`Invalid graph data: ${validation.errors.map(e => e.message).join(', ')}`);
    }

    const allowedTypes = ['node', 'group'];
    const invalidNodes = validation.data.nodes.filter(n => !allowedTypes.includes(n.type));
    
    if (invalidNodes.length > 0) {
      throw new Error(`Invalid node types: ${invalidNodes.map(n => n.type).join(', ')}. Allowed: ${allowedTypes.join(', ')}`);
    }

    return delay(validation.data as GraphPayload);
  },
};
