export type NodePayload = {
  typeId: string;
  value: unknown;
};

export interface ASTNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    typeId: string;
    payload: NodePayload;
    properties: Record<string, string>;
    visualToken?: string;
  };
  parentId?: string;
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
  };
  hidden?: boolean;
}

export interface SemanticAction {
  type: 'CREATE_ELEMENTS' | 'DELETE_ELEMENTS' | 'UPDATE_NODE' | 'UPDATE_EDGE';
  payload: unknown;
  timestamp: number;
  actor?: string;
  affectedIds: string[];
}
