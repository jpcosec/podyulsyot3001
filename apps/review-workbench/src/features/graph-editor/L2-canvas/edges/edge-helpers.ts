import { Position, type Connection } from '@xyflow/react';

const DEFAULT_NODE_WIDTH = 170;
const DEFAULT_NODE_HEIGHT = 68;

type NodeBounds = {
  measured?: { width?: number; height?: number };
  internals?: { positionAbsolute?: { x: number; y: number } };
  positionAbsolute?: { x: number; y: number };
};

type Point = { x: number; y: number };

function getNodeSize(node: NodeBounds): { width: number; height: number } {
  return {
    width: node.measured?.width ?? DEFAULT_NODE_WIDTH,
    height: node.measured?.height ?? DEFAULT_NODE_HEIGHT,
  };
}

function getNodeOrigin(node: NodeBounds): Point {
  return node.internals?.positionAbsolute ?? node.positionAbsolute ?? { x: 0, y: 0 };
}

export function getNodeIntersection(source: NodeBounds, target: NodeBounds): Point {
  const sourceSize = getNodeSize(source);
  const targetSize = getNodeSize(target);
  const sourceOrigin = getNodeOrigin(source);
  const targetOrigin = getNodeOrigin(target);

  const sourceCenterX = sourceOrigin.x + sourceSize.width / 2;
  const sourceCenterY = sourceOrigin.y + sourceSize.height / 2;
  const targetCenterX = targetOrigin.x + targetSize.width / 2;
  const targetCenterY = targetOrigin.y + targetSize.height / 2;

  const w = sourceSize.width / 2;
  const h = sourceSize.height / 2;
  const xx1 = (targetCenterX - sourceCenterX) / (2 * w) - (targetCenterY - sourceCenterY) / (2 * h);
  const yy1 = (targetCenterX - sourceCenterX) / (2 * w) + (targetCenterY - sourceCenterY) / (2 * h);
  const alpha = 1 / (Math.abs(xx1) + Math.abs(yy1));
  const xx3 = alpha * xx1;
  const yy3 = alpha * yy1;

  return {
    x: w * (xx3 + yy3) + sourceCenterX,
    y: h * (-xx3 + yy3) + sourceCenterY,
  };
}

function getEdgePosition(node: NodeBounds, intersectionPoint: Point): Position {
  const origin = getNodeOrigin(node);
  const size = getNodeSize(node);

  const nX = Math.round(origin.x);
  const nY = Math.round(origin.y);
  const pX = Math.round(intersectionPoint.x);
  const pY = Math.round(intersectionPoint.y);

  if (pX <= nX + 1) return Position.Left;
  if (pX >= nX + size.width - 1) return Position.Right;
  if (pY <= nY + 1) return Position.Top;
  return Position.Bottom;
}

export interface EdgeParams {
  sx: number;
  sy: number;
  tx: number;
  ty: number;
  sourcePosition: Position;
  targetPosition: Position;
}

export function getEdgeParams(source: NodeBounds, target: NodeBounds): EdgeParams {
  const sourceIntersection = getNodeIntersection(source, target);
  const targetIntersection = getNodeIntersection(target, source);

  return {
    sx: sourceIntersection.x,
    sy: sourceIntersection.y,
    tx: targetIntersection.x,
    ty: targetIntersection.y,
    sourcePosition: getEdgePosition(source, sourceIntersection),
    targetPosition: getEdgePosition(target, targetIntersection),
  };
}

type ConnectionRegistry = { canConnect: (source: string, target: string) => boolean };

export function isValidConnection(
  connection: Pick<Connection, 'source' | 'target' | 'sourceHandle' | 'targetHandle'>,
  registry: ConnectionRegistry,
): boolean {
  if (connection.sourceHandle && connection.targetHandle) {
    return registry.canConnect(connection.sourceHandle, connection.targetHandle);
  }

  return true;
}
