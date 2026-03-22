import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { PackageFilesPayload } from '../../../types/api.types';

export function usePackageFiles(source: string, jobId: string) {
  return useQuery<PackageFilesPayload>({
    queryKey: ['package-files', source, jobId],
    queryFn: () => apiClient.query.jobs.getPackageFiles(source, jobId),
    staleTime: 30_000,
  });
}
