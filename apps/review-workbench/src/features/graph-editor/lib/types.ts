export interface RawNode {
  id: string;
  type: string;
  name: string;
  properties: Record<string, string>;
  children?: RawNode[];
}

export interface RawEdge {
  id: string;
  source: string;
  target: string;
  relationType: string;
  properties?: Record<string, string>;
}

export interface RawData {
  nodes: RawNode[];
  edges: RawEdge[];
}

export type {
  ASTEdge,
  ASTNode,
  NodePayload,
  ValidationError,
  ValidatedAST,
} from '@/stores/types';

export interface DomainNode {
  id: string;
  type: string;
  name: string;
  properties: Record<string, string>;
  children: DomainNode[];
}

export interface DomainEdge {
  id: string;
  source: string;
  target: string;
  relationType: string;
  properties: Record<string, string>;
}

export interface DomainData {
  nodes: DomainNode[];
  edges: DomainEdge[];
}
