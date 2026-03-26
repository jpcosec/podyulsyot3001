import type { ComponentType } from 'react';

import { z } from 'zod';

import type { NodeTypeDefinition } from './registry.types';

export type RendererZoomLevel = 'dot' | 'label' | 'detail';

const UNKNOWN_TYPE_ERROR_SCHEMA = z
  .unknown()
  .refine(() => false, { message: 'Unknown node type' });

export class NodeTypeRegistry {
  private readonly types = new Map<string, NodeTypeDefinition>();

  register(definition: NodeTypeDefinition): void {
    if (this.types.has(definition.typeId)) {
      console.warn(`Overriding existing node type: ${definition.typeId}`);
    }

    this.types.set(definition.typeId, definition);
  }

  get(typeId: string): NodeTypeDefinition | undefined {
    return this.types.get(typeId);
  }

  getRenderer(typeId: string, zoomLevel: RendererZoomLevel): ComponentType<unknown> {
    const definition = this.types.get(typeId);
    if (!definition) {
      throw new Error(`Unknown node type: ${typeId}`);
    }

    return definition.renderers[zoomLevel] as ComponentType<unknown>;
  }

  validatePayload(typeId: string, payload: unknown): z.SafeParseReturnType<unknown, unknown> {
    const definition = this.types.get(typeId);
    if (!definition) {
      return UNKNOWN_TYPE_ERROR_SCHEMA.safeParse(payload);
    }

    return definition.payloadSchema.safeParse(payload);
  }

  sanitizePayload(typeId: string, payload: unknown): unknown {
    const definition = this.types.get(typeId);
    if (!definition) {
      return payload;
    }

    return definition.sanitizer ? definition.sanitizer(payload) : payload;
  }

  canConnect(sourceTypeId: string, targetTypeId: string): boolean {
    const source = this.types.get(sourceTypeId);
    if (!source) {
      return false;
    }

    return source.allowedConnections.includes(targetTypeId);
  }

  getAll(): NodeTypeDefinition[] {
    return Array.from(this.types.values());
  }
}

export const registry = new NodeTypeRegistry();
