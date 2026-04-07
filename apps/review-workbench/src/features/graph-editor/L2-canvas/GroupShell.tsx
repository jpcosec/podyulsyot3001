import { memo } from 'react';

import { Handle, NodeResizer, NodeToolbar, Position, type Node, type NodeProps } from '@xyflow/react';

import { useEdgeInheritance } from './hooks';
import type { ASTNode, NodePayload } from '@/stores/types';

type CanvasNode = Node<ASTNode['data'], string>;

export const COLLAPSED_KEY = '__collapsed';

function asPayloadRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object') {
    return value as Record<string, unknown>;
  }
  return {};
}

function getGroupTitle(nodeData: ASTNode['data']): string {
  // Handle both AST format and direct JSON format
  const asJson = nodeData as Record<string, unknown>;
  
  // Direct JSON format: data.label
  if ('label' in asJson && typeof asJson.label === 'string') {
    return asJson.label;
  }
  
  // AST format: data.payload.value.name or data.payload.value.title
  const payload = asJson.payload as NodePayload | undefined;
  const payloadRecord = asPayloadRecord(payload?.value ?? {});
  const title = payloadRecord.name ?? payloadRecord.title;
  
  if (typeof title === 'string' && title.trim().length > 0) {
    return title;
  }

  return 'Group';
}

export function isCollapsed(nodeData: ASTNode['data']): boolean {
  // Handle both AST format and direct JSON format
  const asJson = nodeData as Record<string, unknown>;
  const props = asJson.properties as Record<string, string> | undefined;
  if (props && COLLAPSED_KEY in props) {
    return props[COLLAPSED_KEY] === 'true';
  }
  // Check if data has a collapsed property directly (new format)
  if ('collapsed' in asJson) {
    return Boolean(asJson.collapsed);
  }
  return false;
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
  const { collapseGroup, expandGroup } = useEdgeInheritance();
  const collapsed = isCollapsed(data);

  const toggleCollapse = () => {
    if (collapsed) {
      expandGroup(id);
      return;
    }

    collapseGroup(id);
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
