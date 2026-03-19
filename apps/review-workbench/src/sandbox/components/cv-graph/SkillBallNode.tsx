import { Handle, Position, type IsValidConnection, type NodeProps } from "@xyflow/react";

import type { SkillNodeData } from "./types";

const isEntryTarget: IsValidConnection = (connection) => {
  return (connection.target ?? "").startsWith("entry:");
};

const isEntrySource: IsValidConnection = (connection) => {
  return (connection.source ?? "").startsWith("entry:");
};

function shapeClass(shape: SkillNodeData["shape"]): string {
  if (shape === "diamond") {
    return "cv-skill-shape-diamond";
  }
  if (shape === "square") {
    return "cv-skill-shape-square";
  }
  return "cv-skill-shape-circle";
}

export function SkillBallNode(props: NodeProps): JSX.Element {
  const { id, selected } = props;
  const data = props.data as unknown as SkillNodeData;
  const mastery = `${data.masteryLabel} (${data.masteryValue}/5)`;
  return (
    <div className="cv-skill-node-wrap" title={`${data.label} - ${data.category} - ${mastery}`}>
      <Handle
        type="target"
        position={Position.Left}
        isValidConnection={isEntrySource}
        className="cv-skill-handle"
      />

      <button
        type="button"
        className={`cv-skill-node transition-transform duration-150 hover:scale-105 ${shapeClass(data.shape)} ${selected ? "cv-node-selected" : ""} ${
          data.essential ? "cv-skill-node-essential" : ""
        }`}
        style={{ backgroundColor: data.fillColor }}
        onClick={(event) => {
          event.stopPropagation();
          data.onSelectSkill?.(id);
        }}
      >
        <span className="cv-skill-node-short">{data.label.slice(0, 2).toUpperCase()}</span>
      </button>

      <div className="cv-skill-node-caption">
        <span className="cv-skill-name">{data.label}</span>
        <span className="cv-skill-mastery">{mastery}</span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        isValidConnection={isEntryTarget}
        className="cv-skill-handle"
      />
    </div>
  );
}
