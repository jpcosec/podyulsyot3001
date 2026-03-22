import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { ViewPayload } from '../../../types/api.types';

export function useViewExtract(source: string, jobId: string) {
  return useQuery<ViewPayload>({
    queryKey: ['view', 'extract', source, jobId],
    queryFn: () => apiClient.query.jobs.getView(source, jobId, 'extract'),
  });
}
