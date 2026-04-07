import type {
  ASTEdge,
  ASTNode,
  RawData,
  RawEdge,
  RawNode,
  ValidationError,
  ValidatedAST,
} from './types';
import { registry } from '@/schema/registry';
import type { NodeTypeRegistry } from '@/schema/registry';

const X_SPACING = 220;
const Y_SPACING = 140;

type SchemaRegistryAdapter = Pick<NodeTypeRegistry, 'get' | 'validatePayload' | 'sanitizePayload'>;

function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message);
  }

  return 'Validation failed';
}

function toErrorNode(
  nodeId: string,
  parentId: string | undefined,
  position: { x: number; y: number },
  properties: Record<string, string>,
  message: string,
): ASTNode {
  return {
    id: nodeId,
    type: 'error',
    position,
    data: {
      typeId: 'error',
      payload: {
        typeId: 'error',
        value: { message },
      },
      properties,
    },
    parentId,
  };
}

function toValidNode(
  rawNode: RawNode,
  parentId: string | undefined,
  position: { x: number; y: number },
  colorToken: string,
  payloadValue: unknown,
): ASTNode {
  return {
    id: rawNode.id,
    type: 'node',
    position,
    data: {
      typeId: rawNode.type,
      payload: {
        typeId: rawNode.type,
        value: payloadValue,
      },
      properties: rawNode.properties,
      visualToken: colorToken,
    },
    parentId,
  };
}

function matchNodes(rawData: RawData, schemaRegistry: SchemaRegistryAdapter): Map<string, ASTNode> {
  const nodeMap = new Map<string, ASTNode>();
  const depthOffsets = new Map<number, number>();

  const nextPosition = (depth: number) => {
    const offset = depthOffsets.get(depth) ?? 0;
    depthOffsets.set(depth, offset + 1);

    return {
      x: depth * X_SPACING,
      y: offset * Y_SPACING,
    };
  };

  const processNode = (rawNode: RawNode, parentId?: string, depth = 0) => {
    const definition = schemaRegistry.get(rawNode.type);
    const position = nextPosition(depth);

    if (!definition) {
      nodeMap.set(
        rawNode.id,
        toErrorNode(
          rawNode.id,
          parentId,
          position,
          rawNode.properties,
          `Unknown node type: ${rawNode.type}`,
        ),
      );
    } else {
      const payloadCandidate = {
        ...rawNode.properties,
        name: rawNode.name,
        title: rawNode.name,
      };

      const validation = schemaRegistry.validatePayload(rawNode.type, payloadCandidate);

      if (!validation.success) {
        nodeMap.set(
          rawNode.id,
          toErrorNode(
            rawNode.id,
            parentId,
            position,
            rawNode.properties,
            `Validation failed: ${getErrorMessage(validation.error)}`,
          ),
        );
      } else {
        const sanitizedPayload = schemaRegistry.sanitizePayload(rawNode.type, validation.data);

        nodeMap.set(
          rawNode.id,
          toValidNode(rawNode, parentId, position, definition.colorToken, sanitizedPayload),
        );
      }
    }

    rawNode.children?.forEach((childNode) => processNode(childNode, rawNode.id, depth + 1));
  };

  rawData.nodes.forEach((rawNode) => processNode(rawNode));

  return nodeMap;
}

function resolveEdges(rawEdges: RawEdge[], nodeMap: Map<string, ASTNode>): ASTEdge[] {
  return rawEdges
    .filter((rawEdge) => nodeMap.has(rawEdge.source) && nodeMap.has(rawEdge.target))
    .map((rawEdge) => ({
      id: rawEdge.id,
      source: rawEdge.source,
      target: rawEdge.target,
      type: 'floating',
      data: {
        relationType: rawEdge.relationType,
        properties: rawEdge.properties ?? {},
      },
    }));
}

function collectErrors(nodeMap: Map<string, ASTNode>): ValidationError[] {
  const errors: ValidationError[] = [];

  nodeMap.forEach((node, nodeId) => {
    if (node.type !== 'error') {
      return;
    }

    const asJson = node.data as Record<string, unknown>;
    const payload = asJson.payload as { value?: unknown } | undefined;
    const payloadValue = payload?.value;
    const message =
      payloadValue && typeof payloadValue === 'object' && 'message' in payloadValue
        ? String((payloadValue as { message: unknown }).message)
        : 'Validation failed';

    errors.push({ nodeId, message });
  });

  return errors;
}

export function schemaToGraphWithRegistry(
  rawData: RawData,
  schemaRegistry: SchemaRegistryAdapter,
): ValidatedAST {
  const nodeMap = matchNodes(rawData, schemaRegistry);
  const edges = resolveEdges(rawData.edges, nodeMap);

  return {
    nodes: Array.from(nodeMap.values()),
    edges,
    errors: collectErrors(nodeMap),
  };
}

export function schemaToGraph(rawData: RawData): ValidatedAST {
  return schemaToGraphWithRegistry(rawData, registry);
}
