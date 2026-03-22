import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { EvidenceBankPayload } from '../../../types/api.types';

export function useEvidenceBank(source: string, jobId: string) {
  return useQuery<EvidenceBankPayload>({
    queryKey: ['evidence-bank', source, jobId],
    queryFn: () => apiClient.query.jobs.getEvidenceBank(source, jobId),
    staleTime: 30_000,
  });
}
