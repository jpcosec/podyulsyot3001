import graphData from './fixtures/graph_data.json';

const delay = <T>(v: T, ms = 80): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), ms));

export interface GraphPayload {
  nodes: unknown[];
  edges: unknown[];
}

export const mockClient = {
  async getGraph(): Promise<GraphPayload> {
    return delay(graphData as GraphPayload);
  },
};
