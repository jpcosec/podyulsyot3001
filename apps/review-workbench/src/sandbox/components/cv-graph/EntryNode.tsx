import { Handle, Position, type IsValidConnection, type NodeProps } from "@xyflow/react";

import type { EntryNodeData } from "./types";

const isSkillTarget: IsValidConnection = (connection) => {
  return (connection.target ?? "").startsWith("skill:");
};

const isSkillSource: IsValidConnection = (connection) => {
  return (connection.source ?? "").startsWith("skill:");
};

function weightBadge(weight: string): string {
  if (weight === "headline") {
    return "H";
  }
  if (weight === "primary_detail") {
    return "P";
  }
  if (weight === "supporting_detail") {
    return "S";
  }
  return "F";
}

export function EntryNode(props: NodeProps): JSX.Element {
  const { id, selected } = props;
  const data = props.data as unknown as EntryNodeData;
  const isExpanded = data.expanded;

  return (
    <div className="cv-entry-node-wrapper">
      <Handle
        type="target"
        position={Position.Left}
        isValidConnection={isSkillSource}
        className="cv-entry-handle"
      />

      <button
        type="button"
        className={`cv-entry-card transition duration-150 ${isExpanded ? "cv-entry-card-expanded" : ""} ${selected ? "cv-node-selected" : ""}`}
        onClick={(event) => {
          event.stopPropagation();
          data.onToggleExpand(id);
        }}
      >
        <span className="cv-entry-category-strip" aria-hidden="true" />
        <div className="cv-entry-title-wrap">
          <span className="cv-entry-title">{data.label}</span>
          <span className="cv-entry-category-chip">{data.category.replace(/_/g, " ")}</span>
        </div>
        <div className="cv-entry-badges">
          <span className="cv-entry-count-chip">{data.descriptions.length} bullets</span>
          {data.essential ? <span className="cv-entry-essential-chip">Essential</span> : null}
        </div>
      </button>

      {isExpanded ? (
        <div
          className="cv-entry-expand-panel rounded-xl bg-white/95 backdrop-blur-sm nodrag nopan nowheel"
          onClick={(event) => event.stopPropagation()}
        >
          <label className="cv-inline-field">
            <span>Category</span>
            <input
              value={data.category}
              onChange={(event) => data.onUpdateCategory(id, event.target.value)}
              className="nodrag nopan"
            />
          </label>

          <label className="cv-inline-checkbox">
            <input
              type="checkbox"
              checked={data.essential}
              onChange={(event) => data.onToggleEssential(id, event.target.checked)}
              className="nodrag nopan"
            />
            <span>Essential entry</span>
          </label>

          <div className="cv-inline-section">
            <h4>Descriptions</h4>
            {data.descriptions.map((description) => (
              <label className="cv-inline-field" key={description.key}>
                <span>
                  {weightBadge(description.weight)} - {description.key}
                </span>
                <textarea
                  value={description.text}
                  rows={2}
                  onChange={(event) => data.onUpdateDescription(id, description.key, event.target.value)}
                  className="nodrag nopan"
                />
              </label>
            ))}
            <button
              type="button"
              className="cv-plus-button nodrag nopan"
              onClick={() => data.onAddDescription(id)}
            >
              + Add description
            </button>
          </div>

          <div className="cv-inline-section">
            <h4>Connected skills</h4>
            {data.connectedSkillLabels.length ? (
              <div className="cv-inline-skill-pills">
                {data.connectedSkillLabels.map((label) => (
                  <span key={label} className="cv-inline-skill-pill">
                    {label}
                  </span>
                ))}
              </div>
            ) : (
              <p className="cv-muted">No linked skills yet. Drag from this node to a skill ball.</p>
            )}
          </div>
        </div>
      ) : null}

      <Handle
        type="source"
        position={Position.Right}
        isValidConnection={isSkillTarget}
        className="cv-entry-handle"
      />
    </div>
  );
}
