import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

export function EdgeInspector() {
  const focusedEdgeId = useUIStore((state) => state.focusedEdgeId);
  const setFocusedEdge = useUIStore((state) => state.setFocusedEdge);
  const setEditorState = useUIStore((state) => state.setEditorState);

  const edges = useGraphStore((state) => state.edges);
  const updateEdge = useGraphStore((state) => state.updateEdge);

  const edge = useMemo(
    () => edges.find((candidate) => candidate.id === focusedEdgeId) ?? null,
    [edges, focusedEdgeId],
  );

  const [draftRelationType, setDraftRelationType] = useState('linked');

  useEffect(() => {
    if (!edge) {
      setDraftRelationType('linked');
      return;
    }

    setDraftRelationType(edge.data?.relationType ?? 'linked');
  }, [edge]);

  const handleClose = () => {
    setFocusedEdge(null);
    setEditorState('browse');
  };

  const handleSave = () => {
    if (!edge) {
      return;
    }

    updateEdge(edge.id, {
      data: {
        relationType: draftRelationType,
        properties: edge.data?.properties ?? {},
      },
    });

    handleClose();
  };

  const open = focusedEdgeId !== null && edge !== null;
  if (!open || !edge) {
    return null;
  }

  return (
    <Sheet open={open} onOpenChange={(nextOpen) => !nextOpen && handleClose()}>
      <SheetContent side="right" className="flex w-[400px] flex-col sm:max-w-[400px]">
        <SheetHeader>
          <SheetTitle>Edit Edge</SheetTitle>
          <SheetDescription>
            {edge.source} -&gt; {edge.target}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-4 flex-1 space-y-2 overflow-y-auto pr-1">
          <div className="text-sm font-medium">Relation Type</div>
          <Input
            id="edge-relation-type"
            value={draftRelationType}
            onChange={(event) => setDraftRelationType(event.target.value)}
          />
        </div>

        <div className="mt-4 flex gap-2">
          <Button onClick={handleSave}>Save</Button>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
