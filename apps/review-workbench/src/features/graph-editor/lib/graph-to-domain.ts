import type { ASTEdge, ASTNode, DomainData, DomainEdge, DomainNode } from './types';

function getDomainName(node: ASTNode): string {
  const payload = node.data.payload.value;

  if (payload && typeof payload === 'object') {
    const payloadRecord = payload as Record<string, unknown>;
    const name = payloadRecord.name;
    const title = payloadRecord.title;

    if (typeof name === 'string' && name.length > 0) {
      return name;
    }

    if (typeof title === 'string' && title.length > 0) {
      return title;
    }
  }

  return 'Untitled';
}

function toDomainNode(node: ASTNode): DomainNode {
  return {
    id: node.id,
    type: node.data.typeId,
    name: getDomainName(node),
    properties: node.data.properties,
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
