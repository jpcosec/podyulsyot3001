// apps/review-workbench/src/schemas/types.ts

export type RenderAs = 'group' | 'node' | 'attribute';
export type RelationType = 'contains' | 'extends' | 'semantic_edge' | 'references';

export interface SchemaAttribute {
  name: string;
  type: string;
  required: boolean;
  values?: string[];
  note?: string;
}

export interface SchemaChild {
  type: string;
  via: string;
  group_by?: string;
}

export interface SchemaNodeType {
  id: string;
  label: string;
  render_as: RenderAs;
  color_token: string;
  abstract?: boolean;
  variant_of?: string;
  attributes: SchemaAttribute[];
  children?: SchemaChild[];
}

export interface SchemaEdgeType {
  id: string;
  label: string;
  from: string;
  to: string;
  color_token: string;
  animated?: boolean;
  cardinality?: string;
  note?: string;
}

export interface ColorToken {
  border: string;
  bg: string;
}

export interface EdgeColorToken {
  stroke: string;
}

export interface VisualEncoding {
  color_tokens: Record<string, ColorToken>;
  edge_color_tokens: Record<string, EdgeColorToken>;
}

export interface DocumentSchema {
  document: {
    id: string;
    label: string;
    version: string;
    description: string;
    root_type: string;
  };
  node_types: SchemaNodeType[];
  edge_types: SchemaEdgeType[];
  visual_encoding: VisualEncoding;
}
