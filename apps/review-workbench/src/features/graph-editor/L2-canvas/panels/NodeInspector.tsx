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
import type { NodePayload } from '@/stores/types';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

interface NodeInspectorDraft {
  title: string;
  properties: Record<string, string>;
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object') {
    return value as Record<string, unknown>;
  }
  return {};
}

function asDataRecord(data: unknown): Record<string, unknown> {
  if (data && typeof data === 'object') {
    return data as Record<string, unknown>;
  }
  return {};
}

function getNodeTitle(data: Record<string, unknown>): string {
  // Direct JSON format: data.label
  if ('label' in data && typeof data.label === 'string') {
    return data.label;
  }
  // Direct JSON format: data.name
  if ('name' in data && typeof data.name === 'string') {
    return data.name;
  }
  // AST format: payload.name or payload.title
  const title = data.name ?? data.title;
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

    const asJson = asDataRecord(node.data);
    const title = getNodeTitle(asJson);
    const properties = asJson.properties as Record<string, string> | undefined;

    setDraft({
      title,
      properties: properties ?? {},
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

    const asJson = asDataRecord(node.data);
    const existingPayload = asJson.payload as NodePayload | undefined;
    const existingValue = existingPayload?.value;
    const payloadRecord = asRecord(existingValue ?? {});
    
    const safeTypeId = (existingPayload?.typeId ?? asJson.typeId ?? 'unknown') as string;
    const newPayload: NodePayload = {
      typeId: safeTypeId || 'unknown',
      value: setNodeTitle(payloadRecord, draft.title),
    };

    updateNode(node.id, {
      data: {
        ...node.data,
        ...(asJson.label !== undefined ? { label: draft.title } : {}),
        ...(asJson.name !== undefined ? { name: draft.title } : {}),
        payload: newPayload,
        properties: draft.properties,
      },
    });

    handleClose();
  };

  const open = focusedNodeId !== null && node !== null && draft !== null;
  if (!open || !node || !draft) {
    return null;
  }

  const asJson = asDataRecord(node.data);
  const typeId = asJson.typeId as string | undefined;

  return (
    <Sheet open={open} onOpenChange={(nextOpen) => !nextOpen && handleClose()}>
      <SheetContent side="right" className="flex w-[400px] flex-col sm:max-w-[400px]">
        <SheetHeader>
          <SheetTitle>Edit Node</SheetTitle>
          <SheetDescription>
            {typeId ?? 'unknown'} ({node.id})
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
