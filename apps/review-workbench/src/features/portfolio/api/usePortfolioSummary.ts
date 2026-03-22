import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../../api/client';

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: () => apiClient.query.portfolio.getSummary(),
    staleTime: 60_000,
  });
}
