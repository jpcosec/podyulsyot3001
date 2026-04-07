/** Node payload envelope for AST nodes */
export type NodePayload = {
  /** Type identifier matching registry node type */
  typeId?: string;
  /** Arbitrary payload value (validated by registry) */
  value?: unknown;
};

/** Node data structure - supports both AST and direct JSON formats */
export type NodeData = {
  /** Type identifier from registry */
  typeId?: string;
  /** AST payload envelope */
  payload?: NodePayload;
  /** Key-value properties */
  properties?: Record<string, string>;
  /** Visual token for color theming */
  visualToken?: string;
  /** Direct JSON format: node label */
  label?: string;
  /** Direct JSON format: node name */
  name?: string;
  /** Additional properties */
  [key: string]: unknown;
};

/** Abstract Syntax Tree Node */
export interface ASTNode {
  /** Unique node identifier */
  id: string;
  /** Node type (node, group, error) */
  type: string;
  /** Position on canvas */
  position: { x: number; y: number };
  /** Node data */
  data: NodeData;
  /** Parent node for grouping */
  parentId?: string;
  /** Extent behavior for groups */
  extent?: 'parent' | string;
  /** CSS styles */
  style?: React.CSSProperties;
  /** Selection state */
  selected?: boolean;
  /** Visibility */
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
