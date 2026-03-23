import { Outlet, useParams, NavLink } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';

const PIPELINE_STEPS = [
  { label: 'Flow',       path: '' },
  { label: 'Scrape',     path: 'scrape' },
  { label: 'Translate',  path: 'translate' },
  { label: 'Extract',    path: 'extract' },
  { label: 'Match',      path: 'match' },
  { label: 'Sculpt',     path: 'sculpt' },
  { label: 'Deployment', path: 'deployment' },
];

export function JobWorkspaceShell() {
  const { source, jobId } = useParams();
  const base = `/jobs/${source}/${jobId}`;

  return (
    <div className="flex flex-col min-h-full">
      <header className="h-10 flex items-center justify-between px-4 border-b border-outline/10 bg-surface shrink-0">
        <div className="flex items-center gap-2 text-[11px] font-mono text-on-muted">
          <NavLink to="/" className="hover:text-primary transition-colors">Portfolio</NavLink>
          <ChevronRight size={12} />
          <span>{source}</span>
          <ChevronRight size={12} />
          <span className="text-primary">{jobId}</span>
        </div>

        <nav className="flex items-center gap-1">
          {PIPELINE_STEPS.map(({ label, path }) => (
            <NavLink
              key={path}
              to={path ? `${base}/${path}` : base}
              end={path === ''}
              className={({ isActive }) =>
                cn(
                  'px-3 py-1 text-[10px] font-mono uppercase tracking-widest transition-colors',
                  isActive
                    ? 'text-primary border-b border-primary'
                    : 'text-on-muted hover:text-on-surface',
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
