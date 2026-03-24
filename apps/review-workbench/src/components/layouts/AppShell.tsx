import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderOpen, Network, GitGraph, Layers } from 'lucide-react';
import { cn } from '../../utils/cn';

const NAV_ITEMS = [
  { to: '/',         icon: LayoutDashboard, label: 'Portfolio', end: true },
  { to: '/explorer', icon: FolderOpen,      label: 'Explorer',  end: false },
  { to: '/cv',       icon: Network,         label: 'Base CV',   end: false },
  { to: '/graph',    icon: GitGraph,        label: 'Graph',     end: false },
  { to: '/schema',   icon: Layers,          label: 'Schema',    end: false },
];

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-background">
      <nav className="fixed left-0 top-0 h-full w-14 bg-surface flex flex-col items-center py-4 gap-2 border-r border-outline/10 z-50">
        <div className="w-7 h-7 mb-4 border border-primary/40 flex items-center justify-center">
          <span className="text-primary font-mono text-[10px] font-bold">P2</span>
        </div>

        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'w-10 h-10 flex items-center justify-center transition-colors group relative',
                isActive ? 'text-primary tactical-glow' : 'text-on-muted hover:text-on-surface',
              )
            }
          >
            <Icon size={18} />
            <span className="absolute left-full ml-2 px-2 py-1 bg-surface-high text-on-surface text-[10px] font-mono uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
              {label}
            </span>
          </NavLink>
        ))}


      </nav>

      <main className="ml-14 flex-1 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
