import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';

export function useJobTimeline(source: string, jobId: string) {
  return useQuery({
    queryKey: ['timeline', source, jobId],
    queryFn: () => apiClient.query.jobs.getTimeline(source, jobId),
    staleTime: 30_000,
  });
}
