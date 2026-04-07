import { memo, useState } from 'react';

import { BaseEdge, EdgeLabelRenderer, getBezierPath, useStore, type EdgeProps } from '@xyflow/react';

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
  const [isHovered, setIsHovered] = useState(false);

  if (!sourceNode || !targetNode) {
    return null;
  }

  const relationType = readRelationType(data);

  const params = getEdgeParams(sourceNode, targetNode);
  const [path, labelX, labelY] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  const isInherited = relationType === 'inherited';

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        style={getInheritedStyle(style, relationType)}
        markerEnd={isInherited ? undefined : markerEnd}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className={`px-1 py-0.5 text-[10px] rounded bg-background/90 border text-muted-foreground transition-opacity ${
            isHovered || relationType ? 'opacity-100' : 'opacity-0'
          }`}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {relationType || 'linked'}
        </div>
      </EdgeLabelRenderer>
    </>
  );
});
