import { memo, useCallback, useState } from 'react';

import { EdgeLabelRenderer, getBezierPath, useStore, type EdgeProps } from '@xyflow/react';

import { useGraphStore } from '@/stores/graph-store';

import { FloatingEdge } from './FloatingEdge';
import { getEdgeParams } from './edge-helpers';

type DeleteEdgeParams = {
  edgeId: string;
  onDelete: ((edgeId: string) => void) | null;
  removeElements: (nodeIds: string[], edgeIds: string[]) => void;
};

export function shouldShowDeleteButton(selected: boolean | undefined, labelHovered: boolean, edgeHovered: boolean): boolean {
  return Boolean(selected) || labelHovered || edgeHovered;
}

export function deleteEdge({ edgeId, onDelete, removeElements }: DeleteEdgeParams): void {
  if (onDelete) {
    onDelete(edgeId);
    return;
  }

  removeElements([], [edgeId]);
}

function readDeleteHandler(data: EdgeProps['data']): ((edgeId: string) => void) | null {
  if (!data || typeof data !== 'object') {
    return null;
  }

  const onDelete = (data as { onDelete?: unknown }).onDelete;
  return typeof onDelete === 'function' ? (onDelete as (edgeId: string) => void) : null;
}

export const ButtonEdge = memo(function ButtonEdge({ id, source, target, selected, data, ...rest }: EdgeProps) {
  const [isLabelHovered, setIsLabelHovered] = useState(false);
  const [isEdgeHovered, setIsEdgeHovered] = useState(false);
  const removeElements = useGraphStore((state) => state.removeElements);

  const sourceNode = useStore((store) => store.nodeLookup.get(source));
  const targetNode = useStore((store) => store.nodeLookup.get(target));
  const onDelete = readDeleteHandler(data);

  const handleDelete = useCallback(() => {
    deleteEdge({ edgeId: id, onDelete, removeElements });
  }, [id, onDelete, removeElements]);

  if (!sourceNode || !targetNode) {
    return null;
  }

  const params = getEdgeParams(sourceNode, targetNode);
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  const showButton = shouldShowDeleteButton(selected, isLabelHovered, isEdgeHovered);

  return (
    <>
      <FloatingEdge id={id} source={source} target={target} selected={selected} data={data} {...rest} />
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={24}
        pointerEvents="stroke"
        onMouseEnter={() => setIsEdgeHovered(true)}
        onMouseLeave={() => setIsEdgeHovered(false)}
      />
      <EdgeLabelRenderer>
        <div
          className="nodrag nopan"
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: 'all',
          }}
          onMouseEnter={() => setIsLabelHovered(true)}
          onMouseLeave={() => setIsLabelHovered(false)}
        >
          <button
            type="button"
            onClick={handleDelete}
            className={
              showButton
                ? 'h-5 w-5 rounded border border-border bg-background text-xs text-muted-foreground transition-colors hover:border-destructive hover:bg-destructive hover:text-destructive-foreground'
                : 'hidden'
            }
            aria-label="Delete edge"
          >
            x
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});
