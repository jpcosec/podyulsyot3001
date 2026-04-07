import { Button } from '@/components/ui/button';
import { useGraphStore } from '@/stores/graph-store';
import type { ASTNode, NodePayload } from '@/stores/types';
import { useUIStore } from '@/stores/ui-store';
import { toast } from 'sonner';

function cloneValue<T>(value: T): T {
  if (value === null || value === undefined) {
    return value;
  }

  if (typeof structuredClone === 'function') {
    return structuredClone(value);
  }

  return JSON.parse(JSON.stringify(value)) as T;
}

function makeCopyNode(node: ASTNode): ASTNode {
  const asJson = node.data as Record<string, unknown>;
  const existingPayload = asJson.payload as NodePayload | undefined;
  
  return {
    ...node,
    id: `node-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    position: {
      x: node.position.x + 48,
      y: node.position.y + 48,
    },
    selected: false,
    data: {
      ...node.data,
      payload: existingPayload ? {
        ...existingPayload,
        value: cloneValue(existingPayload.value),
      } : undefined,
      properties: { ...(asJson.properties as Record<string, string> ?? {}) },
    },
  };
}

interface ActionsSectionProps {
  onSave: () => void;
}

export function ActionsSection({ onSave }: ActionsSectionProps) {
  const nodes = useGraphStore((state) => state.nodes);
  const edges = useGraphStore((state) => state.edges);
  const undoStack = useGraphStore((state) => state.undoStack);
  const redoStack = useGraphStore((state) => state.redoStack);
  const isDirty = useGraphStore((state) => state.isDirty());
  const addElements = useGraphStore((state) => state.addElements);
  const removeElements = useGraphStore((state) => state.removeElements);
  const undo = useGraphStore((state) => state.undo);
  const redo = useGraphStore((state) => state.redo);

  const copiedNodeId = useUIStore((state) => state.copiedNodeId);
  const copyNode = useUIStore((state) => state.copyNode);
  const openDeleteConfirm = useUIStore((state) => state.openDeleteConfirm);

  const selectedNode = nodes.find((node) => node.selected);
  const selectedNodeIds = nodes.filter((node) => node.selected).map((node) => node.id);
  const selectedEdgeIds = edges.filter((edge) => edge.selected).map((edge) => edge.id);

  const handleSave = () => {
    onSave();
    toast.success('Graph saved successfully');
  };

  const handleCopy = () => {
    if (!selectedNode) {
      toast.info('Select a node to copy');
      return;
    }

    copyNode(selectedNode.id);
    toast.success('Node copied to clipboard');
  };

  const handlePaste = () => {
    if (!copiedNodeId) {
      toast.info('No copied node available');
      return;
    }

    const sourceNode = nodes.find((node) => node.id === copiedNodeId);
    if (!sourceNode) {
      toast.error('Copied node is no longer available');
      return;
    }

    addElements([makeCopyNode(sourceNode)], []);
    toast.success('Node pasted');
  };

  const handleDelete = () => {
    if (selectedNodeIds.length === 0 && selectedEdgeIds.length === 0) {
      toast.info('Select nodes or edges to delete');
      return;
    }

    if (selectedNodeIds.length > 0) {
      const nodeTitles = selectedNodeIds.map(id => {
        const node = nodes.find(n => n.id === id);
        return node?.data.visualToken ?? id;
      }).join(', ');
      openDeleteConfirm({
        kind: 'node',
        title: nodeTitles,
        description: selectedNodeIds.length === 1 
          ? `This will permanently delete "${nodeTitles}" and all its connections.`
          : `This will permanently delete ${selectedNodeIds.length} nodes and all their connections.`,
      }, selectedNodeIds, selectedEdgeIds);
    } else {
      const edgeTitles = selectedEdgeIds.map(id => {
        const edge = edges.find(e => e.id === id);
        return edge?.data?.relationType ?? id;
      }).join(', ');
      openDeleteConfirm({
        kind: 'edge',
        title: edgeTitles,
        description: `This will permanently delete ${selectedEdgeIds.length} edge(s).`,
      }, selectedNodeIds, selectedEdgeIds);
    }
  };

  return (
    <div className="flex flex-col gap-2 px-3 pb-3">
      <Button size="sm" onClick={handleSave} disabled={!isDirty}>
        Save
      </Button>
      <div className="flex gap-1">
        <Button size="sm" variant="outline" onClick={undo} className="flex-1" disabled={undoStack.length === 0}>
          Undo
        </Button>
        <Button size="sm" variant="outline" onClick={redo} className="flex-1" disabled={redoStack.length === 0}>
          Redo
        </Button>
      </div>
      <div className="flex gap-1">
        <Button size="sm" variant="outline" onClick={handleCopy} className="flex-1">
          Copy
        </Button>
        <Button size="sm" variant="outline" onClick={handlePaste} className="flex-1" disabled={!copiedNodeId}>
          Paste
        </Button>
      </div>
      <Button
        size="sm"
        variant="destructive"
        onClick={handleDelete}
        disabled={selectedNodeIds.length === 0 && selectedEdgeIds.length === 0}
      >
        Delete
      </Button>
    </div>
  );
}
