import cvSchema from '../../../schemas/cv.schema.json';
import jobSchema from '../../../schemas/job.schema.json';
import matchSchema from '../../../schemas/match.schema.json';
import type { DocumentSchema } from '../../../schemas/types';

export type SchemaDomain = 'cv' | 'job' | 'match';

const SCHEMAS: Record<SchemaDomain, DocumentSchema> = {
  cv: cvSchema as unknown as DocumentSchema,
  job: jobSchema as unknown as DocumentSchema,
  match: matchSchema as unknown as DocumentSchema,
};

export function useSchema(domain: SchemaDomain): DocumentSchema {
  return SCHEMAS[domain];
}
