import { mockClient, type GraphPayload } from '@/mock/client';

interface SchemaAttribute {
  type: string;
  required: boolean;
}

interface SchemaNodeType {
  id: string;
  display_name: string;
  visual: {
    color_token: string;
    icon: string;
  };
  attributes: Record<string, SchemaAttribute>;
}

export interface GraphSchema {
  node_types: SchemaNodeType[];
}

export interface GraphDataProvider {
  getSchema: () => Promise<GraphSchema>;
  getGraph: () => Promise<GraphPayload>;
  saveGraph: (payload: GraphPayload) => Promise<{ ok: true }>;
}

const mockSchema: GraphSchema = {
  node_types: [
    {
      id: 'entity',
      display_name: 'Entity',
      visual: {
        color_token: 'surface-primary',
        icon: 'circle',
      },
      attributes: {
        name: { type: 'string', required: true },
      },
    },
  ],
};

export const graphDataProvider: GraphDataProvider = {
  async getSchema() {
    return mockSchema;
  },
  async getGraph() {
    return mockClient.getGraph();
  },
  async saveGraph() {
    return { ok: true };
  },
};
