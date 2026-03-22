import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { ArtifactListPayload } from '../../../types/api.types';

export function useArtifacts(source: string, jobId: string, nodeName: string) {
  return useQuery<ArtifactListPayload>({
    queryKey: ['artifacts', source, jobId, nodeName],
    queryFn: () => apiClient.query.jobs.getArtifacts(source, jobId, nodeName),
  });
}
