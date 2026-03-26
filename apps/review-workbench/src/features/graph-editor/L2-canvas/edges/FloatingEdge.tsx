import { memo } from 'react';

import { BaseEdge, getBezierPath, useStore, type EdgeProps } from '@xyflow/react';

import { getEdgeParams } from './edge-helpers';

function readRelationType(data: EdgeProps['data']): string | undefined {
  if (!data || typeof data !== 'object') {
    return undefined;
  }

  const relationType = (data as { relationType?: unknown }).relationType;
  return typeof relationType === 'string' ? relationType : undefined;
}

function getInheritedStyle(
  style: EdgeProps['style'],
  relationType: string | undefined,
): EdgeProps['style'] {
  if (relationType !== 'inherited') {
    return style;
  }

  return {
    ...style,
    strokeDasharray: '3 4',
    opacity: 0.5,
    stroke: style?.stroke ?? 'rgba(116, 117, 120, 0.7)',
  };
}

export const FloatingEdge = memo(function FloatingEdge({
  id,
  source,
  target,
  style,
  markerEnd,
  data,
}: EdgeProps) {
  const sourceNode = useStore((store) => store.nodeLookup.get(source));
  const targetNode = useStore((store) => store.nodeLookup.get(target));

  if (!sourceNode || !targetNode) {
    return null;
  }

  const relationType = readRelationType(data);

  const params = getEdgeParams(sourceNode, targetNode);
  const [path] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  const isInherited = relationType === 'inherited';

  return (
    <BaseEdge
      id={id}
      path={path}
      style={getInheritedStyle(style, relationType)}
      markerEnd={isInherited ? undefined : markerEnd}
    />
  );
});
