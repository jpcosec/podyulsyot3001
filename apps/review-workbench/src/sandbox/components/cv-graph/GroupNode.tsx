import type { NodeProps } from "@xyflow/react";

import type { GroupNodeData } from "./types";

export function GroupNode(props: NodeProps): JSX.Element {
  const data = props.data as unknown as GroupNodeData;
  return (
    <div className="cv-group-node-wrap">
      <button
        type="button"
        className="cv-group-header transition duration-150 hover:brightness-110 nodrag nopan"
        onClick={(event) => {
          event.stopPropagation();
          data.onToggleGroup(data.category);
        }}
      >
        <span className="cv-group-title">{data.label}</span>
        <span className="cv-group-meta">
          <span className="cv-group-count">{data.count}</span>
          <span className="cv-group-chevron">{data.expanded ? "▼" : "▶"}</span>
        </span>
      </button>

      {data.expanded ? (
        <button
          type="button"
          className="cv-plus-button cv-group-plus nodrag nopan"
          onClick={(event) => {
            event.stopPropagation();
            data.onAddItem(data.category);
          }}
        >
          + {data.addLabel}
        </button>
      ) : null}
    </div>
  );
}
