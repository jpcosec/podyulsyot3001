import type { ReactNode } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { PanelRightClose, PanelRightOpen, Sparkles } from 'lucide-react';

import { useUIStore } from '@/stores/ui-store';

import { ActionsSection } from './ActionsSection';
import { CreationSection } from './CreationSection';
import { FiltersSection } from './FiltersSection';
import { ViewSection } from './ViewSection';

const accordionClassName = 'px-4 font-mono text-[10px] uppercase tracking-[0.24em]';

interface CanvasSidebarProps {
  onSave: () => void;
}

function AccordionPanel({
  value,
  title,
  children,
}: {
  value: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <AccordionItem value={value} className="section-card overflow-hidden rounded-[1.25rem] border-none px-0">
      <AccordionTrigger className={accordionClassName}>{title}</AccordionTrigger>
      <AccordionContent>{children}</AccordionContent>
    </AccordionItem>
  );
}

export function CanvasSidebar({ onSave }: CanvasSidebarProps) {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);

  if (!sidebarOpen) {
    return (
      <aside className="ml-4 flex h-full w-14 items-start justify-center">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="glass-panel mt-6 h-11 w-11 rounded-2xl border-white/10 bg-surface/80"
          onClick={toggleSidebar}
          aria-label="Open sidebar"
        >
          <PanelRightOpen className="h-4 w-4" />
        </Button>
      </aside>
    );
  }

  return (
    <aside className="ml-4 h-full w-[320px] overflow-y-auto rounded-[2rem]">
      <div className="glass-panel h-full rounded-[2rem]">
        <div className="border-b border-white/8 px-5 py-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-primary">
                <Sparkles className="h-4 w-4" />
                <span className="font-mono text-[10px] uppercase tracking-[0.24em]">Editor Deck</span>
              </div>
              <h2 className="mt-3 font-headline text-2xl font-bold text-on-surface">Control surface</h2>
              <p className="mt-1 text-sm text-muted-foreground">Build, filter, and save without losing sight of the graph.</p>
            </div>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-10 w-10 rounded-2xl border border-white/8 bg-white/[0.03]"
              onClick={toggleSidebar}
              aria-label="Close sidebar"
            >
              <PanelRightClose className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-4 p-4">
          <div className="section-card rounded-[1.5rem] px-4 py-3">
            <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-muted-foreground">Flow</p>
            <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xl font-semibold text-on-surface">Live</p>
                <p className="text-xs text-muted-foreground">Interactive graph session</p>
              </div>
              <div>
                <p className="text-xl font-semibold text-on-surface">Studio</p>
                <p className="text-xs text-muted-foreground">Panels tuned for editing speed</p>
              </div>
            </div>
          </div>

          <Accordion type="multiple" defaultValue={['actions', 'filters', 'creation', 'view']} className="space-y-3 px-1 pb-4">
            <AccordionPanel value="actions" title="Actions">
              <ActionsSection onSave={onSave} />
            </AccordionPanel>

            <AccordionPanel value="filters" title="Filters">
              <FiltersSection />
            </AccordionPanel>

            <AccordionPanel value="creation" title="Creation">
              <CreationSection />
            </AccordionPanel>

            <AccordionPanel value="view" title="View">
              <ViewSection />
            </AccordionPanel>
          </Accordion>
        </div>
      </div>
    </aside>
  );
}
