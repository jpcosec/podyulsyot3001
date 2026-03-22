import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { ViewPayload } from '../../../types/api.types';

export function useViewMatch(source: string, jobId: string) {
  return useQuery<ViewPayload>({
    queryKey: ['view', 'match', source, jobId],
    queryFn: () => apiClient.query.jobs.getView(source, jobId, 'match'),
    staleTime: 30_000,
  });
}
