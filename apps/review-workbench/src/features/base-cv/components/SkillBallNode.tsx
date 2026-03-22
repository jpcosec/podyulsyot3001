import { Handle, Position, type IsValidConnection, type NodeProps } from "@xyflow/react";
import { cn } from '../../../utils/cn';
import type { SkillNodeData } from "./types";

const isEntryTarget: IsValidConnection = (connection) => {
  return (connection.target ?? "").startsWith("entry:");
};

const isEntrySource: IsValidConnection = (connection) => {
  return (connection.source ?? "").startsWith("entry:");
};

function shapeClass(shape: SkillNodeData["shape"]): string {
  if (shape === "diamond") return "rotate-45";
  if (shape === "square") return "rounded-sm";
  return "rounded-full";
}

export function SkillBallNode(props: NodeProps): JSX.Element {
  const { id, selected } = props;
  const data = props.data as unknown as SkillNodeData;
  const mastery = `${data.masteryLabel} (${data.masteryValue}/5)`;

  return (
    <div
      className="flex flex-col items-center gap-1"
      title={`${data.label} - ${data.category} - ${mastery}`}
    >
      <Handle
        type="target"
        position={Position.Left}
        isValidConnection={isEntrySource}
        className="!bg-primary/50 !border-primary/30 !w-1.5 !h-1.5"
      />

      <button
        type="button"
        className={cn(
          "w-10 h-10 flex items-center justify-center text-xs font-bold text-white font-mono cursor-pointer transition-transform duration-150 hover:scale-105",
          shapeClass(data.shape),
          selected && "ring-2 ring-primary/80",
          data.essential && "ring-2 ring-primary"
        )}
        style={{ backgroundColor: data.fillColor }}
        onClick={(event) => {
          event.stopPropagation();
          data.onSelectSkill?.(id);
        }}
      >
        <span className="pointer-events-none">
          {data.shape === "diamond" ? (
            <span className="-rotate-45 inline-block">{data.label.slice(0, 2).toUpperCase()}</span>
          ) : (
            data.label.slice(0, 2).toUpperCase()
          )}
        </span>
      </button>

      <div className="flex flex-col items-center">
        <span className="font-mono text-[9px] text-on-surface text-center leading-tight">
          {data.label}
        </span>
        <span className="font-mono text-[8px] text-on-muted/60 text-center leading-tight">
          {mastery}
        </span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        isValidConnection={isEntryTarget}
        className="!bg-primary/50 !border-primary/30 !w-1.5 !h-1.5"
      />
    </div>
  );
}
