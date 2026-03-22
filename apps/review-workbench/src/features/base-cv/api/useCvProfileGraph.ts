import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { CvProfileGraphPayload } from '../../../types/api.types';

export function useCvProfileGraph() {
  return useQuery<CvProfileGraphPayload>({
    queryKey: ['cv-profile-graph'],
    queryFn: () => apiClient.query.profile.getCvProfileGraph(),
  });
}

export function useSaveCvGraph() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CvProfileGraphPayload) =>
      apiClient.commands.profile.saveCvProfileGraph(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cv-profile-graph'] }),
  });
}
