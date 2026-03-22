import { Handle, Position, type IsValidConnection, type NodeProps } from "@xyflow/react";
import { cn } from '../../../utils/cn';
import type { EntryNodeData } from "./types";

const isSkillTarget: IsValidConnection = (connection) => {
  return (connection.target ?? "").startsWith("skill:");
};

const isSkillSource: IsValidConnection = (connection) => {
  return (connection.source ?? "").startsWith("skill:");
};

function weightBadge(weight: string): string {
  if (weight === "headline") return "H";
  if (weight === "primary_detail") return "P";
  if (weight === "supporting_detail") return "S";
  return "F";
}

export function EntryNode(props: NodeProps): JSX.Element {
  const { id, selected } = props;
  const data = props.data as unknown as EntryNodeData;
  const isExpanded = data.expanded;

  return (
    <div className="relative">
      <Handle
        type="target"
        position={Position.Left}
        isValidConnection={isSkillSource}
        className="!bg-primary !border-primary/50 !w-2 !h-2"
      />

      <button
        type="button"
        className={cn(
          "bg-surface-container border border-outline/30 border-l-4 border-l-primary px-3 py-2 w-full text-left cursor-pointer transition duration-150 flex flex-col gap-1",
          isExpanded && "border-primary/80",
          selected && "ring-1 ring-primary/60 shadow-[0_0_8px_rgba(0,242,255,0.25)]"
        )}
        onClick={(event) => {
          event.stopPropagation();
          data.onToggleExpand(id);
        }}
      >
        <div className="flex items-center justify-between gap-2">
          <span className="font-headline font-semibold text-sm text-on-surface leading-tight truncate">
            {data.label}
          </span>
          <span className="font-mono text-[8px] text-on-muted/60 shrink-0">
            {data.category.replace(/_/g, " ")}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="font-mono text-[8px] text-on-muted/60 border border-outline/20 px-1 py-0.5">
            {data.descriptions.length} bullets
          </span>
          {data.essential ? (
            <span className="font-mono text-[8px] text-green-400 border border-green-500/40 px-1 py-0.5">
              Essential
            </span>
          ) : null}
        </div>
      </button>

      {isExpanded ? (
        <div
          className="absolute left-0 top-full mt-1 w-[300px] z-30 bg-surface-container border border-outline/30 p-3 shadow-lg flex flex-col gap-2 nodrag nopan nowheel"
          onClick={(event) => event.stopPropagation()}
        >
          <label className="flex flex-col gap-1">
            <span className="font-mono text-[9px] text-on-muted uppercase">Category</span>
            <input
              value={data.category}
              onChange={(event) => data.onUpdateCategory(id, event.target.value)}
              className="bg-surface-high border border-outline/30 px-2 py-1 font-mono text-xs text-on-surface focus:outline-none focus:border-primary/60 w-full nodrag nopan"
            />
          </label>

          <label className="flex items-center gap-2 font-mono text-xs text-on-surface cursor-pointer">
            <input
              type="checkbox"
              checked={data.essential}
              onChange={(event) => data.onToggleEssential(id, event.target.checked)}
              className="nodrag nopan"
            />
            <span>Essential entry</span>
          </label>

          <div className="flex flex-col gap-1.5">
            <h4 className="font-mono text-[9px] text-on-muted uppercase tracking-widest">
              Descriptions
            </h4>
            {data.descriptions.map((description) => (
              <label className="flex flex-col gap-1" key={description.key}>
                <span className="font-mono text-[9px] text-on-muted uppercase">
                  {weightBadge(description.weight)} - {description.key}
                </span>
                <textarea
                  value={description.text}
                  rows={2}
                  onChange={(event) =>
                    data.onUpdateDescription(id, description.key, event.target.value)
                  }
                  className="bg-surface-high border border-outline/30 px-2 py-1 font-mono text-xs text-on-surface focus:outline-none focus:border-primary/60 w-full nodrag nopan"
                />
              </label>
            ))}
            <button
              type="button"
              className="font-mono text-[10px] text-primary/70 hover:text-primary transition-colors text-left nodrag nopan"
              onClick={() => data.onAddDescription(id)}
            >
              + Add description
            </button>
          </div>

          <div className="flex flex-col gap-1.5">
            <h4 className="font-mono text-[9px] text-on-muted uppercase tracking-widest">
              Connected skills
            </h4>
            {data.connectedSkillLabels.length ? (
              <div className="flex flex-wrap gap-1">
                {data.connectedSkillLabels.map((label) => (
                  <span
                    key={label}
                    className="font-mono text-[9px] text-on-surface border border-outline/30 px-1.5 py-0.5"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : (
              <p className="font-mono text-[9px] text-on-muted/60 italic">
                No linked skills yet. Drag from this node to a skill ball.
              </p>
            )}
          </div>
        </div>
      ) : null}

      <Handle
        type="source"
        position={Position.Right}
        isValidConnection={isSkillTarget}
        className="!bg-primary !border-primary/50 !w-2 !h-2"
      />
    </div>
  );
}
