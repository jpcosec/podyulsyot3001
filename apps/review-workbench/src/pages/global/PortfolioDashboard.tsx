import { usePortfolioSummary } from '../../features/portfolio/api/usePortfolioSummary';
import { PortfolioTable } from '../../features/portfolio/components/PortfolioTable';

export function PortfolioDashboard() {
  const { data, isLoading, isError } = usePortfolioSummary();
  return (
    <div className="p-6">
      <p className="font-mono text-[10px] text-primary uppercase tracking-widest">System / PhD 2.0</p>
      <h1 className="font-headline text-xl font-bold text-on-surface mt-1 mb-6">Application Portfolio</h1>
      <PortfolioTable data={data} loading={isLoading} error={isError} />
    </div>
  );
}
