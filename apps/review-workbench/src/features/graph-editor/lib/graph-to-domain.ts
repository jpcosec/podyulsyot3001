import type { ASTEdge, ASTNode, DomainData, DomainEdge, DomainNode, NodePayload } from './types';

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object') {
    return value as Record<string, unknown>;
  }
  return {};
}

function getDomainName(node: ASTNode): string {
  const asJson = node.data as Record<string, unknown>;
  
  // Direct JSON format: data.label or data.name
  if ('label' in asJson && typeof asJson.label === 'string' && asJson.label.length > 0) {
    return asJson.label;
  }
  if ('name' in asJson && typeof asJson.name === 'string' && asJson.name.length > 0) {
    return asJson.name;
  }

  // AST format: data.payload.value
  const payload = asJson.payload as NodePayload | undefined;
  const payloadRecord = asRecord(payload?.value);
  const name = payloadRecord.name;
  const title = payloadRecord.title;

  if (typeof name === 'string' && name.length > 0) {
    return name;
  }

  if (typeof title === 'string' && title.length > 0) {
    return title;
  }

  return 'Untitled';
}

function toDomainNode(node: ASTNode): DomainNode {
  const asJson = node.data as Record<string, unknown>;
  const typeId = asJson.typeId as string | undefined;
  const properties = asJson.properties as Record<string, string> | undefined;
  
  return {
    id: node.id,
    type: typeId ?? 'unknown',
    name: getDomainName(node),
    properties: properties ?? {},
    children: [],
  };
}

function toDomainEdge(edge: ASTEdge): DomainEdge {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    relationType: edge.data?.relationType ?? 'linked',
    properties: edge.data?.properties ?? {},
  };
}

function wouldCreateParentCycle(
  nodeId: string,
  parentId: string,
  parentById: Map<string, string | undefined>
): boolean {
  const visited = new Set<string>();
  let currentId: string | undefined = parentId;

  while (currentId) {
    if (currentId === nodeId) {
      return true;
    }

    if (visited.has(currentId)) {
      return false;
    }

    visited.add(currentId);
    currentId = parentById.get(currentId);
  }

  return false;
}

export function graphToDomain(nodes: ASTNode[], edges: ASTEdge[]): DomainData {
  const nodeById = new Map<string, DomainNode>();
  const parentById = new Map<string, string | undefined>();
  const rootNodes: DomainNode[] = [];

  nodes.forEach((node) => {
    if (node.type === 'error') {
      return;
    }

    nodeById.set(node.id, toDomainNode(node));
    parentById.set(node.id, node.parentId);
  });

  nodes.forEach((node) => {
    if (node.type === 'error') {
      return;
    }

    const currentNode = nodeById.get(node.id);
    if (!currentNode) {
      return;
    }

    if (node.parentId && node.parentId !== node.id) {
      const parentNode = nodeById.get(node.parentId);
      if (parentNode && !wouldCreateParentCycle(node.id, node.parentId, parentById)) {
        parentNode.children.push(currentNode);
        return;
      }
    }

    rootNodes.push(currentNode);
  });

  return {
    nodes: rootNodes,
    edges: edges
      .filter((edge) => nodeById.has(edge.source) && nodeById.has(edge.target))
      .map(toDomainEdge),
  };
}
