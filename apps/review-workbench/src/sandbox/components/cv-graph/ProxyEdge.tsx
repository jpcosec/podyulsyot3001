import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";

export function ProxyEdge(props: EdgeProps): JSX.Element {
  const [path] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
  });

  const isProxy = Boolean((props.data as { proxy?: boolean } | undefined)?.proxy);

  return (
    <BaseEdge
      id={props.id}
      path={path}
      markerEnd={props.markerEnd}
      style={
        isProxy
          ? {
              ...(props.style ?? {}),
              strokeDasharray: "6 4",
              opacity: 0.72,
            }
          : props.style
      }
    />
  );
}
