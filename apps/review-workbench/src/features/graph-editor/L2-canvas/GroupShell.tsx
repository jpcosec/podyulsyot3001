import { memo } from 'react';

import { Handle, NodeResizer, NodeToolbar, Position, type Node, type NodeProps } from '@xyflow/react';

import { useGraphStore } from '@/stores/graph-store';
import type { ASTNode } from '@/stores/types';

type CanvasNode = Node<ASTNode['data'], string>;

export const COLLAPSED_KEY = '__collapsed';

function asPayloadRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

function getGroupTitle(nodeData: ASTNode['data']): string {
  const payload = asPayloadRecord(nodeData.payload.value);
  const title = payload.name ?? payload.title;

  if (typeof title === 'string' && title.trim().length > 0) {
    return title;
  }

  return 'Group';
}

export function isCollapsed(nodeData: ASTNode['data']): boolean {
  return nodeData.properties[COLLAPSED_KEY] === 'true';
}

export function getNextCollapseProperties(
  properties: ASTNode['data']['properties'],
  collapsed: boolean,
): ASTNode['data']['properties'] {
  return {
    ...properties,
    [COLLAPSED_KEY]: String(!collapsed),
  };
}

export const GroupShell = memo(function GroupShell({ id, data, selected }: NodeProps<CanvasNode>) {
  const updateNode = useGraphStore((state) => state.updateNode);
  const collapsed = isCollapsed(data);

  const toggleCollapse = () => {
    updateNode(id, {
      data: {
        ...data,
        properties: getNextCollapseProperties(data.properties, collapsed),
      },
    });
  };

  return (
    <>
      <NodeToolbar position={Position.Top} align="start" isVisible>
        <div className="flex items-center gap-2 rounded border bg-background px-2 py-1 text-xs">
          <button onClick={toggleCollapse} className="transition-colors hover:text-primary">
            {collapsed ? 'Expand' : 'Collapse'}
          </button>
          <span className="font-semibold">{getGroupTitle(data)}</span>
        </div>
      </NodeToolbar>

      <div
        className="h-full w-full rounded-lg border-2 border-dashed bg-transparent"
        style={{ borderColor: 'var(--token-section, #666)' }}
      >
        <NodeResizer
          isVisible={selected && !collapsed}
          minWidth={160}
          minHeight={60}
          handleClassName="!bg-primary"
        />

        {!collapsed ? (
          <>
            <Handle
              type="target"
              position={Position.Top}
              className="!border-muted-foreground !bg-muted-foreground"
            />
            <Handle
              type="source"
              position={Position.Bottom}
              className="!border-muted-foreground !bg-muted-foreground"
            />
          </>
        ) : null}
      </div>
    </>
  );
});
