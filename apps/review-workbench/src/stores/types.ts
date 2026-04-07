export type NodePayload = {
  typeId?: string;
  value?: unknown;
};

export type NodeData = {
  typeId?: string;
  payload?: NodePayload;
  properties?: Record<string, string>;
  visualToken?: string;
  label?: string;
  name?: string;
  [key: string]: unknown;
};

export interface ASTNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: NodeData;
  parentId?: string;
  extent?: 'parent' | string;
  style?: React.CSSProperties;
  selected?: boolean;
  hidden?: boolean;
}

export interface ASTEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data?: {
    relationType: string;
    properties: Record<string, string>;
    _originalSource?: string;
    _originalTarget?: string;
    _originalRelationType?: string;
  };
  selected?: boolean;
  hidden?: boolean;
}

export interface ValidationError {
  nodeId: string;
  message: string;
}

export interface ValidatedAST {
  nodes: ASTNode[];
  edges: ASTEdge[];
  errors: ValidationError[];
}

export interface SemanticAction {
  type: 'CREATE_ELEMENTS' | 'DELETE_ELEMENTS' | 'UPDATE_NODE' | 'UPDATE_EDGE';
  payload: unknown;
  timestamp: number;
  actor?: string;
  affectedIds: string[];
}
