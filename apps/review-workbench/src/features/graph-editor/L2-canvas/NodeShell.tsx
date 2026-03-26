import { memo, useMemo, type ComponentType } from 'react';

import { Handle, Position, useStore, type Node, type NodeProps } from '@xyflow/react';

import { registry } from '@/schema/registry';
import type { ASTNode } from '@/stores/types';

type CanvasNode = Node<ASTNode['data'], string>;

const ZOOM_DETAIL = 0.9;
const ZOOM_LABEL = 0.4;

const zoomSelector = (state: { transform: [number, number, number] }) => state.transform[2];

function asPayloadRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

export function getNodeTitle(data: ASTNode['data']): string {
  const payloadRecord = asPayloadRecord(data.payload.value);
  const title = payloadRecord.name ?? payloadRecord.title;

  return typeof title === 'string' && title.trim().length > 0 ? title : 'Untitled';
}

export function getUnknownMessage(data: ASTNode['data']): string | null {
  const payloadRecord = asPayloadRecord(data.payload.value);
  const message = payloadRecord.message;

  return typeof message === 'string' && message.trim().length > 0 ? message : null;
}

export function getRenderTier(zoom: number): 'detail' | 'label' | 'dot' {
  if (zoom >= ZOOM_DETAIL) {
    return 'detail';
  }

  if (zoom >= ZOOM_LABEL) {
    return 'label';
  }

  return 'dot';
}

function renderNodeBody(data: ASTNode['data'], colorToken: string, zoom: number) {
  const definition = registry.get(data.typeId);
  if (!definition) {
    return null;
  }

  const payloadRecord = asPayloadRecord(data.payload.value);
  const title = getNodeTitle(data);
  const tier = getRenderTier(zoom);

  if (tier === 'detail') {
    const DetailRenderer = definition.renderers.detail as ComponentType<Record<string, unknown>>;
    const detailProps = {
      ...payloadRecord,
      title,
      category: definition.label,
      properties: data.properties,
      visualToken: data.visualToken,
      colorToken,
    };

    return <DetailRenderer {...detailProps} />;
  }

  if (tier === 'label') {
    const LabelRenderer = definition.renderers.label;
    return <LabelRenderer title={title} icon={definition.icon} />;
  }

  const DotRenderer = definition.renderers.dot;
  return <DotRenderer colorToken={colorToken} />;
}

export const NodeShell = memo(function NodeShell(props: NodeProps<CanvasNode>) {
  const zoom = useStore(zoomSelector);
  const { data } = props;

  const definition = registry.get(data.typeId);
  const colorToken = definition?.colorToken ?? 'token-error';
  const nodeBody = useMemo(() => renderNodeBody(data, colorToken, zoom), [data, colorToken, zoom]);

  if (!definition) {
    const message = getUnknownMessage(data);
    return (
      <div className="min-w-[150px] rounded-lg border-2 border-red-500 bg-red-50 p-2">
        <span className="text-xs text-red-600">Unknown: {data.typeId}</span>
        {message ? <p className="text-[10px] text-red-400">{message}</p> : null}
        <Handle type="target" position={Position.Top} />
        <Handle type="source" position={Position.Bottom} />
      </div>
    );
  }

  return (
    <div
      className={`rounded-lg border-2 bg-card ${props.selected ? 'ring-2 ring-primary/40' : ''}`}
      style={{
        borderColor: `var(--${definition.colorToken}, #888)`,
        minWidth: definition.defaultSize.width,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!border-muted-foreground !bg-muted-foreground"
      />

      {nodeBody}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!border-muted-foreground !bg-muted-foreground"
      />
    </div>
  );
});
