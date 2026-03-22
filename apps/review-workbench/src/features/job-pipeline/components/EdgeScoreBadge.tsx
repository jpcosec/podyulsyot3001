import { BaseEdge, EdgeLabelRenderer, getStraightPath } from '@xyflow/react';
import { cn } from '../../../utils/cn';

interface Props {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  data?: { score?: number | null; edgeType?: 'llm' | 'manual' };
  selected?: boolean;
}

export function EdgeScoreBadge({ id, sourceX, sourceY, targetX, targetY, data, selected }: Props) {
  const [edgePath, labelX, labelY] = getStraightPath({ sourceX, sourceY, targetX, targetY });
  const score = data?.score ?? null;
  const isManual = data?.edgeType === 'manual';
  const strokeColor = isManual ? '#fecb00' : '#00f2ff';

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: strokeColor,
          strokeWidth: selected ? 2 : 1,
          strokeDasharray: '6 3',
          opacity: 0.7,
        }}
      />
      {score !== null && (
        <EdgeLabelRenderer>
          <div
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)` }}
            className={cn(
              'absolute pointer-events-none font-mono font-black text-[9px] px-1 py-0.5 border',
              isManual
                ? 'bg-secondary/20 text-secondary border-secondary/40'
                : 'bg-primary/20 text-primary border-primary/40'
            )}
          >
            {Math.round(score * 100)}%
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
