import { useEffect, useMemo, useState } from 'react';

import { PropertyEditor } from '@/components/content/PropertyEditor';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { pairsFromRecord, recordFromPairs } from '@/lib/utils';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

interface NodeInspectorDraft {
  title: string;
  properties: Record<string, string>;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

function getNodeTitle(payload: Record<string, unknown>): string {
  const title = payload.name ?? payload.title;
  return typeof title === 'string' ? title : '';
}

function setNodeTitle(payload: Record<string, unknown>, title: string): Record<string, unknown> {
  if ('title' in payload && !('name' in payload)) {
    return { ...payload, title };
  }

  return { ...payload, name: title };
}

export function NodeInspector() {
  const focusedNodeId = useUIStore((state) => state.focusedNodeId);
  const setFocusedNode = useUIStore((state) => state.setFocusedNode);
  const setEditorState = useUIStore((state) => state.setEditorState);

  const nodes = useGraphStore((state) => state.nodes);
  const updateNode = useGraphStore((state) => state.updateNode);

  const node = useMemo(
    () => nodes.find((candidate) => candidate.id === focusedNodeId) ?? null,
    [focusedNodeId, nodes],
  );

  const [draft, setDraft] = useState<NodeInspectorDraft | null>(null);

  useEffect(() => {
    if (!node) {
      setDraft(null);
      return;
    }

    const payload = asRecord(node.data.payload.value);
    setDraft({
      title: getNodeTitle(payload),
      properties: { ...node.data.properties },
    });
  }, [node]);

  const handleClose = () => {
    setFocusedNode(null);
    setEditorState('browse');
  };

  const handleSave = () => {
    if (!node || !draft) {
      return;
    }

    const payload = asRecord(node.data.payload.value);
    updateNode(node.id, {
      data: {
        ...node.data,
        payload: {
          typeId: node.data.payload.typeId,
          value: setNodeTitle(payload, draft.title),
        },
        properties: draft.properties,
      },
    });

    handleClose();
  };

  const open = focusedNodeId !== null && node !== null && draft !== null;
  if (!open || !node || !draft) {
    return null;
  }

  return (
    <Sheet open={open} onOpenChange={(nextOpen) => !nextOpen && handleClose()}>
      <SheetContent side="right" className="flex w-[400px] flex-col sm:max-w-[400px]">
        <SheetHeader>
          <SheetTitle>Edit Node</SheetTitle>
          <SheetDescription>
            {node.data.typeId} ({node.id})
          </SheetDescription>
        </SheetHeader>

        <div className="mt-4 flex-1 space-y-4 overflow-y-auto pr-1">
          <div className="space-y-2">
            <div className="text-sm font-medium">Name</div>
            <Input
              id="node-name"
              value={draft.title}
              onChange={(event) => setDraft((current) => (current ? { ...current, title: event.target.value } : current))}
            />
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium">Properties</div>
            <PropertyEditor
              pairs={pairsFromRecord(draft.properties)}
              onChange={(pairs) =>
                setDraft((current) =>
                  current
                    ? {
                        ...current,
                        properties: recordFromPairs(pairs),
                      }
                    : current,
                )
              }
            />
          </div>
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
