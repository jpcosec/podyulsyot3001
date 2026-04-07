import type { ReactNode } from 'react';
import { GitGraph, Orbit, Sparkles } from 'lucide-react';
import { cn } from '../../utils/cn';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-grid relative flex min-h-screen bg-background">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,170,0,0.12),transparent_22%),radial-gradient(circle_at_20%_20%,rgba(0,242,255,0.1),transparent_28%)]" />
      <nav className="glass-panel fixed left-4 top-4 z-50 flex h-[calc(100vh-2rem)] w-16 flex-col items-center justify-between rounded-[1.75rem] px-2 py-4">
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10 shadow-[0_0_30px_rgba(0,242,255,0.12)]">
            <span className="font-mono text-xs font-bold tracking-[0.3em] text-primary">P2</span>
          </div>

          <div className="flex flex-col gap-2">
            <div
              className={cn(
                'group relative flex h-11 w-11 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary tactical-glow'
              )}
            >
              <GitGraph size={18} />
              <span className="absolute left-full ml-3 whitespace-nowrap rounded-full border border-white/10 bg-surface-high/90 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.28em] text-on-surface opacity-100 pointer-events-none">
                Graph
              </span>
            </div>

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/8 bg-white/[0.03] text-muted-foreground">
              <Orbit size={16} />
            </div>
          </div>
        </div>

        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-secondary/20 bg-secondary/10 text-secondary alert-glow">
          <Sparkles size={16} />
        </div>
      </nav>

      <main className="relative ml-24 flex-1 min-h-screen">
        {children}
      </main>
    </div>
  );
}
