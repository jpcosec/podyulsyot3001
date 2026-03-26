import type { ComponentType } from 'react';

import type { z } from 'zod';

export interface NodeTypeDefinition {
  typeId: string;
  label: string;
  icon: string;
  category: string;
  colorToken: string;
  payloadSchema: z.ZodSchema;
  sanitizer?: (payload: unknown) => unknown;
  renderers: {
    dot: ComponentType<{ colorToken: string }>;
    label: ComponentType<{ title: string; icon: string }>;
    detail: ComponentType<unknown>;
  };
  defaultSize: {
    width: number;
    height: number;
  };
  allowedConnections: string[];
}

export interface PayloadSchema {
  [key: string]: z.ZodTypeAny;
}
