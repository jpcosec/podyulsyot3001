import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/ui-store';

import { ActionsSection } from './ActionsSection';
import { CreationSection } from './CreationSection';
import { FiltersSection } from './FiltersSection';
import { ViewSection } from './ViewSection';

const accordionClassName = 'font-mono text-[10px] uppercase tracking-[0.2em] px-3';

interface CanvasSidebarProps {
  onSave: () => void;
}

export function CanvasSidebar({ onSave }: CanvasSidebarProps) {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);

  if (!sidebarOpen) {
    return (
      <aside className="flex h-full w-10 items-start justify-center border-l bg-background p-1">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={toggleSidebar}
          aria-label="Open sidebar"
        >
          ☰
        </Button>
      </aside>
    );
  }

  return (
    <aside className="h-full w-[280px] border-l bg-background overflow-y-auto">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em]">Editor</span>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={toggleSidebar}
          aria-label="Close sidebar"
        >
          ×
        </Button>
      </div>

      <Accordion type="multiple" defaultValue={['actions', 'filters', 'creation', 'view']}>
        <AccordionItem value="actions">
          <AccordionTrigger className={accordionClassName}>Actions</AccordionTrigger>
          <AccordionContent>
            <ActionsSection onSave={onSave} />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="filters">
          <AccordionTrigger className={accordionClassName}>Filters</AccordionTrigger>
          <AccordionContent>
            <FiltersSection />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="creation">
          <AccordionTrigger className={accordionClassName}>Creation</AccordionTrigger>
          <AccordionContent>
            <CreationSection />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="view">
          <AccordionTrigger className={accordionClassName}>View</AccordionTrigger>
          <AccordionContent>
            <ViewSection />
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </aside>
  );
}
