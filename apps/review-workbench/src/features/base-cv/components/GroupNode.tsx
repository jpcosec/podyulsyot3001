import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from '../../../utils/cn';
import type { GroupNodeData } from "./types";

export function GroupNode(props: NodeProps): JSX.Element {
  const data = props.data as unknown as GroupNodeData;

  return (
    <div
      className={cn(
        "bg-surface-container flex flex-col min-w-[200px]",
        data.isDropzoneActive
          ? "border border-primary/60 bg-primary/5"
          : "border border-outline/20"
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-outline/40 !border-outline !w-2 !h-2"
      />

      <button
        type="button"
        className="flex items-center justify-between w-full px-3 py-2 bg-surface-container border-b border-outline/20 font-mono text-[10px] uppercase tracking-widest text-on-muted hover:brightness-110 transition nodrag nopan"
        onClick={(event) => {
          event.stopPropagation();
          data.onToggleGroup(data.category);
        }}
        onDoubleClick={(event) => {
          event.stopPropagation();
          data.onToggleGroup(data.category);
        }}
      >
        <span className="text-on-surface font-semibold">{data.label}</span>
        <span className="flex items-center gap-2">
          <span
            role="button"
            tabIndex={0}
            className="text-primary/60 hover:text-primary cursor-pointer nodrag nopan"
            onClick={(event) => {
              event.stopPropagation();
              data.onSelectGroup?.(data.category);
            }}
            onKeyDown={(event) => {
              if (event.key !== "Enter" && event.key !== " ") return;
              event.preventDefault();
              event.stopPropagation();
              data.onSelectGroup?.(data.category);
            }}
          >
            Edit
          </span>
          <span className="text-on-muted/60">
            {data.count} {data.countLabel}
          </span>
          <span className="text-on-muted">{data.expanded ? "▼" : "▶"}</span>
        </span>
      </button>

      {data.expanded ? (
        <button
          type="button"
          className="w-full text-left px-3 py-1.5 font-mono text-[10px] text-primary/70 hover:text-primary hover:bg-primary/5 border-t border-outline/15 transition-colors nodrag nopan"
          onClick={(event) => {
            event.stopPropagation();
            data.onAddItem(data.category);
          }}
        >
          + {data.addLabel}
        </button>
      ) : null}

      <Handle
        type="source"
        position={Position.Right}
        className="!bg-outline/40 !border-outline !w-2 !h-2"
      />
    </div>
  );
}
