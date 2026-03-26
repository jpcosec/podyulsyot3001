import { z } from 'zod';

export const nodePositionSchema = z.object({
  x: z.number(),
  y: z.number(),
});

export const nodeDataSchema = z.object({
  name: z.string().optional(),
  title: z.string().optional(),
  category: z.string().optional(),
  properties: z.record(z.string(), z.string()).optional(),
  visualToken: z.string().optional(),
});

export const astNodeSchema = z.object({
  id: z.string(),
  type: z.enum(['node', 'group']),
  position: nodePositionSchema,
  data: nodeDataSchema,
  parentId: z.string().optional(),
  extent: z.enum(['parent', 'absolute']).optional(),
  style: z.record(z.string(), z.union([z.number(), z.string()])).optional(),
  selected: z.boolean().optional(),
  hidden: z.boolean().optional(),
});

export const astEdgeDataSchema = z.object({
  relationType: z.string(),
  properties: z.record(z.string(), z.string()).optional(),
  _originalSource: z.string().optional(),
  _originalTarget: z.string().optional(),
  _originalRelationType: z.string().optional(),
});

export const astEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  type: z.string().optional(),
  data: astEdgeDataSchema.optional(),
  selected: z.boolean().optional(),
  hidden: z.boolean().optional(),
});

export const graphPayloadSchema = z.object({
  nodes: z.array(astNodeSchema),
  edges: z.array(astEdgeSchema),
});

export type ValidatedGraphData = z.infer<typeof graphPayloadSchema>;

export function validateGraphData(data: unknown): {
  success: boolean;
  data?: ValidatedGraphData;
  errors: Array<{ path: string; message: string }>;
} {
  const result = graphPayloadSchema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data, errors: [] };
  }

  const errors = result.error.issues.map((issue) => ({
    path: issue.path.join('.'),
    message: issue.message,
  }));

  return { success: false, errors };
}
