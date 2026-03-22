import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';
import type { ExplorerPayload } from '../../../types/api.types';

export function useExplorerBrowse(path: string) {
  return useQuery<ExplorerPayload>({
    queryKey: ['explorer', path],
    queryFn: () => apiClient.query.explorer.browse(path),
  });
}
