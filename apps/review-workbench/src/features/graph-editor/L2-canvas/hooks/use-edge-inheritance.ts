import { useCallback } from 'react';

import { useGraphStore } from '@/stores/graph-store';
import type { ASTEdge, ASTNode } from '@/stores/types';

const COLLAPSED_KEY = '__collapsed';
const INHERITED_RELATION_TYPE = 'inherited';

type UpdateNode = (nodeId: string, patch: Partial<ASTNode>, options?: { isVisualOnly?: boolean }) => void;
type UpdateEdge = (edgeId: string, patch: Partial<ASTEdge>, options?: { isVisualOnly?: boolean }) => void;

export interface EdgeInheritanceState {
  nodes: ASTNode[];
  edges: ASTEdge[];
  updateNode: UpdateNode;
  updateEdge: UpdateEdge;
}

function withCollapsedState(
  data: ASTNode['data'],
  collapsed: boolean,
): ASTNode['data'] {
  return {
    ...data,
    properties: {
      ...data.properties,
      [COLLAPSED_KEY]: String(collapsed),
    },
  };
}

export interface UseEdgeInheritanceResult {
  collapseGroup: (groupId: string) => void;
  expandGroup: (groupId: string) => void;
}

export function collapseGroupEdges(groupId: string, state: EdgeInheritanceState): void {
  const { nodes, edges, updateNode, updateEdge } = state;

  const childNodes = nodes.filter((node) => node.parentId === groupId);
  const childIds = new Set(childNodes.map((node) => node.id));

  childNodes.forEach((node) => {
    updateNode(node.id, { hidden: true }, { isVisualOnly: true });
  });

  edges
    .filter((edge) => childIds.has(edge.source) || childIds.has(edge.target))
    .forEach((edge) => {
      const nextSource = childIds.has(edge.source) ? groupId : edge.source;
      const nextTarget = childIds.has(edge.target) ? groupId : edge.target;

      if (nextSource === nextTarget) {
        return;
      }

      const originalRelationType = edge.data?._originalRelationType ?? edge.data?.relationType ?? 'linked';

      updateEdge(
        edge.id,
        {
          source: nextSource,
          target: nextTarget,
          hidden: edge.hidden,
          data: {
            relationType: INHERITED_RELATION_TYPE,
            properties: edge.data?.properties ?? {},
            _originalSource: edge.data?._originalSource ?? edge.source,
            _originalTarget: edge.data?._originalTarget ?? edge.target,
            _originalRelationType: originalRelationType,
          },
        },
        { isVisualOnly: true },
      );
    });

  const groupNode = nodes.find((node) => node.id === groupId);
  if (!groupNode) {
    return;
  }

  updateNode(
    groupId,
    {
      data: withCollapsedState(groupNode.data, true),
    },
    { isVisualOnly: true },
  );
}

export function expandGroupEdges(groupId: string, state: EdgeInheritanceState): void {
  const { nodes, edges, updateNode, updateEdge } = state;

  const childNodes = nodes.filter((node) => node.parentId === groupId);
  const childIds = new Set(childNodes.map((node) => node.id));

  childNodes.forEach((node) => {
    updateNode(node.id, { hidden: false }, { isVisualOnly: true });
  });

  edges
    .filter((edge) => {
      const hasOriginal = edge.data?._originalSource || edge.data?._originalTarget;
      if (!hasOriginal) {
        return false;
      }

      return (
        edge.source === groupId ||
        edge.target === groupId ||
        childIds.has(edge.data?._originalSource ?? '') ||
        childIds.has(edge.data?._originalTarget ?? '')
      );
    })
    .forEach((edge) => {
      updateEdge(
        edge.id,
        {
          source: edge.data?._originalSource ?? edge.source,
          target: edge.data?._originalTarget ?? edge.target,
          hidden: edge.hidden,
          data: {
            relationType: edge.data?._originalRelationType ?? edge.data?.relationType ?? 'linked',
            properties: edge.data?.properties ?? {},
            _originalSource: undefined,
            _originalTarget: undefined,
            _originalRelationType: undefined,
          },
        },
        { isVisualOnly: true },
      );
    });

  const groupNode = nodes.find((node) => node.id === groupId);
  if (!groupNode) {
    return;
  }

  updateNode(
    groupId,
    {
      data: withCollapsedState(groupNode.data, false),
    },
    { isVisualOnly: true },
  );
}

export function useEdgeInheritance(): UseEdgeInheritanceResult {
  const nodes = useGraphStore((state) => state.nodes);
  const edges = useGraphStore((state) => state.edges);
  const updateNode = useGraphStore((state) => state.updateNode);
  const updateEdge = useGraphStore((state) => state.updateEdge);

  const collapseGroup = useCallback(
    (groupId: string) => {
      collapseGroupEdges(groupId, { nodes, edges, updateNode, updateEdge });
    },
    [edges, nodes, updateEdge, updateNode],
  );

  const expandGroup = useCallback(
    (groupId: string) => {
      expandGroupEdges(groupId, { nodes, edges, updateNode, updateEdge });
    },
    [edges, nodes, updateEdge, updateNode],
  );

  return { collapseGroup, expandGroup };
}
