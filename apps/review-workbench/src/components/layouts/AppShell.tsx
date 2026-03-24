import { GitGraph } from 'lucide-react';
import { cn } from '../../utils/cn';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-background">
      <nav className="fixed left-0 top-0 h-full w-14 bg-surface flex flex-col items-center py-4 gap-2 border-r border-outline/10 z-50">
        <div className="w-7 h-7 mb-4 border border-primary/40 flex items-center justify-center">
          <span className="text-primary font-mono text-[10px] font-bold">P2</span>
        </div>

        <div
          className={cn(
            'w-10 h-10 flex items-center justify-center transition-colors group relative text-primary tactical-glow'
          )}
        >
          <GitGraph size={18} />
          <span className="absolute left-full ml-2 px-2 py-1 bg-surface-high text-on-surface text-[10px] font-mono uppercase tracking-widest opacity-100 whitespace-nowrap pointer-events-none z-50">
            Graph
          </span>
        </div>
      </nav>

      <main className="ml-14 flex-1 min-h-screen">
        {children}
      </main>
    </div>
  );
}
