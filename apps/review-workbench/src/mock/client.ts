import graphData from './fixtures/graph_data.json';
import { validateGraphData } from '@/schema/graph-validation';

const delay = <T>(v: T, ms = 80): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), ms));

export const mockClient = {
  async getGraph() {
    const validation = validateGraphData(graphData);
    
    if (!validation.success || !validation.data) {
      console.error('Graph data validation errors:', validation.errors);
      throw new Error(`Invalid graph data: ${validation.errors.map(e => e.message).join(', ')}`);
    }

    return delay(validation.data);
  },
};
