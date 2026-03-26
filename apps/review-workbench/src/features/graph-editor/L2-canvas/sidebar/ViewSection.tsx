import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useUIStore } from '@/stores/ui-store';
import { toast } from 'sonner';

type LayoutMode = 'auto' | 'manual';

export function ViewSection() {
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('manual');

  const focusedNodeId = useUIStore((state) => state.focusedNodeId);
  const setEditorState = useUIStore((state) => state.setEditorState);
  const setFilter = useUIStore((state) => state.setFilter);

  const applyLayout = () => {
    toast.info('Auto layout will be available in GRP-001-09');
  };

  const focusOnSelected = () => {
    if (!focusedNodeId) {
      return;
    }

    setFilter({ hideNonNeighbors: true });
    setEditorState('focus');
  };

  return (
    <div className="px-3 pb-3">
      <Tabs value={layoutMode} onValueChange={(value) => setLayoutMode(value as LayoutMode)}>
        <TabsList className="w-full">
          <TabsTrigger value="auto" className="flex-1">
            Auto
          </TabsTrigger>
          <TabsTrigger value="manual" className="flex-1">
            Manual
          </TabsTrigger>
        </TabsList>

        <TabsContent value="auto" className="mt-2 space-y-2">
          <Button size="sm" className="w-full" onClick={applyLayout}>
            Apply Layout
          </Button>
          <p className="text-[10px] text-muted-foreground">ELK worker wiring lands in GRP-001-09 hooks.</p>
        </TabsContent>

        <TabsContent value="manual" className="mt-2">
          <p className="text-xs text-muted-foreground">Drag nodes freely and use Undo/Redo for semantic moves.</p>
        </TabsContent>
      </Tabs>

      <div className="mt-3 border-t pt-3">
        <Button
          size="sm"
          variant="outline"
          className="w-full"
          onClick={focusOnSelected}
          disabled={!focusedNodeId}
        >
          Focus on Selected
        </Button>
      </div>
    </div>
  );
}
