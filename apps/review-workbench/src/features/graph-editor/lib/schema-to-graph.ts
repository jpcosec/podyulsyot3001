import type {
  ASTEdge,
  ASTNode,
  RawData,
  RawEdge,
  RawNode,
  SchemaNodeDefinition,
  SchemaRegistry,
  SchemaValidationResult,
  ValidationError,
  ValidatedAST,
} from './types';

const X_SPACING = 220;
const Y_SPACING = 140;

const DEFAULT_RUNTIME_NODE_DEFINITIONS: SchemaNodeDefinition[] = [
  {
    typeId: 'entity',
    colorToken: 'surface-primary',
    validate: validateNodePayload,
  },
  {
    typeId: 'group',
    colorToken: 'surface-primary',
    validate: validateNodePayload,
  },
  {
    typeId: 'simple',
    colorToken: 'surface-primary',
    validate: validateNodePayload,
  },
];

function validateNodePayload(payload: unknown): SchemaValidationResult {
  if (!payload || typeof payload !== 'object') {
    return {
      success: false,
      error: { message: 'Payload must be an object' },
    };
  }

  const candidate = payload as Record<string, unknown>;
  if (typeof candidate.name !== 'string' || candidate.name.trim().length === 0) {
    return {
      success: false,
      error: { message: 'Name is required' },
    };
  }

  return {
    success: true,
    data: candidate,
  };
}

function createSchemaRegistry(definitions: SchemaNodeDefinition[]): SchemaRegistry {
  const definitionMap = new Map(definitions.map((definition) => [definition.typeId, definition]));

  return {
    get(typeId: string) {
      return definitionMap.get(typeId);
    },
  };
}

const runtimeSchemaRegistry = createSchemaRegistry(DEFAULT_RUNTIME_NODE_DEFINITIONS);

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
  definition: SchemaNodeDefinition,
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
      visualToken: definition.colorToken,
    },
    parentId,
  };
}

function matchNodes(rawData: RawData, schemaRegistry: SchemaRegistry): Map<string, ASTNode> {
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
      const validation = definition.validate({
        ...rawNode.properties,
        name: rawNode.name,
      });

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
        const sanitizedPayload = definition.sanitize
          ? definition.sanitize(validation.data)
          : validation.data;

        nodeMap.set(
          rawNode.id,
          toValidNode(rawNode, parentId, position, definition, sanitizedPayload),
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

    const payloadValue = node.data.payload.value;
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
  schemaRegistry: SchemaRegistry,
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
  return schemaToGraphWithRegistry(rawData, runtimeSchemaRegistry);
}
