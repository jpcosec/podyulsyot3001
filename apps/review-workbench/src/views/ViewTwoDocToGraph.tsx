import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { getEditorState, getViewTwoPayload, saveEditorState } from "../api/client";
import { GraphCanvas } from "../components/GraphCanvas";
import type { RequirementItem, ViewTwoPayload } from "../types/models";

const PRIORITY_COLORS: Record<string, string> = {
  must: "#ff7254",
  nice: "#fecb00",
};

export function ViewTwoDocToGraph(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [payload, setPayload] = useState<ViewTwoPayload | null>(null);
  const [selectedRequirementId, setSelectedRequirementId] = useState<string>("");
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [error, setError] = useState<string>("");

  const [editingRequirementId, setEditingRequirementId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState<string>("");
  const [editingSaving, setEditingSaving] = useState<boolean>(false);
  const [editingError, setEditingError] = useState<string>("");

  useEffect(() => {
    getViewTwoPayload(source, jobId)
      .then((data) => {
        setError("");
        setPayload(data);
        if (data.requirements[0]) {
          setSelectedRequirementId(data.requirements[0].id);
        } else {
          setError("No extracted requirements available for this job yet.");
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [source, jobId]);

  const selectedRequirement = useMemo<RequirementItem | null>(
    () => payload?.requirements.find((item) => item.id === selectedRequirementId) ?? null,
    [payload, selectedRequirementId],
  );

  const sourceLines = payload?.source_markdown.split("\n") ?? [];
  const highlightedLines = new Set(
    selectedRequirement?.spans.flatMap((span) => {
      const output: number[] = [];
      for (let line = span.start_line; line <= span.end_line; line += 1) {
        output.push(line);
      }
      return output;
    }) ?? [],
  );

  const graphNodes = [
    { id: "source", label: "Source Document" },
    ...(payload?.requirements.map((req) => ({ id: req.id, label: req.id })) ?? []),
  ];
  const graphEdges =
    payload?.requirements.map((req) => ({
      source: "source",
      target: req.id,
      label: req.priority,
    })) ?? [];

  const activeNodeIds = selectedRequirement ? [selectedRequirement.id] : [];

  const selectRequirementFromLine = (lineNumber: number): void => {
    setSelectedLine(lineNumber);
    if (!payload) {
      return;
    }
    const linked = payload.requirements.find((requirement) =>
      requirement.spans.some((span) => lineNumber >= span.start_line && lineNumber <= span.end_line),
    );
    if (linked) {
      setSelectedRequirementId(linked.id);
    }
  };

  const handleStartEdit = (req: RequirementItem): void => {
    setEditingRequirementId(req.id);
    setEditingText(req.text);
    setEditingError("");
  };

  const handleCancelEdit = (): void => {
    setEditingRequirementId(null);
    setEditingText("");
    setEditingError("");
  };

  const handleSaveEdit = async (): Promise<void> => {
    if (!editingRequirementId || !payload) return;
    setEditingSaving(true);
    setEditingError("");
    try {
      const updatedRequirements = payload.requirements.map((req) =>
        req.id === editingRequirementId ? { ...req, text: editingText } : req
      );
      const currentState = await getEditorState(source, jobId, "extract_understand");
      const updatedState = { ...currentState.state, requirements: updatedRequirements };
      await saveEditorState(source, jobId, "extract_understand", updatedState);
      const refreshed = await getViewTwoPayload(source, jobId);
      setPayload(refreshed);
      setEditingRequirementId(null);
      setEditingText("");
    } catch (err) {
      setEditingError(err instanceof Error ? err.message : "save failed");
    } finally {
      setEditingSaving(false);
    }
  };

  return (
    <section className="panel split-grid">
      <div>
        <h2>View 2: Document to Graph</h2>
        <p>Review extraction against source text with requirement-linked spans.</p>
        {error ? <p className="error">{error}</p> : null}
        <div className="source-doc">
          {sourceLines.length === 0 ? <p>Loading source text...</p> : null}
          {sourceLines.map((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted = highlightedLines.has(lineNumber);
            const isSelected = selectedLine === lineNumber;
            return (
              <button
                type="button"
                key={`${lineNumber}-${line}`}
                className={`source-line${isHighlighted ? " source-line-highlight" : ""}${
                  isSelected ? " source-line-selected" : ""
                }`}
                onClick={() => selectRequirementFromLine(lineNumber)}
              >
                <span className="source-line-no">{lineNumber}</span>
                <span className="source-line-text">{line || " "}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div>
        <h2>Extracted Requirements</h2>
        {editingError ? <p className="error">{editingError}</p> : null}
        <div className="requirements-list">
          {(payload?.requirements ?? []).map((requirement) => (
            <div
              key={requirement.id}
              className={`requirement-item${
                requirement.id === selectedRequirementId ? " requirement-item-active" : ""
              }${requirement.id === editingRequirementId ? " requirement-item-editing" : ""}`}
              onClick={() => {
                if (editingRequirementId !== requirement.id) {
                  setSelectedRequirementId(requirement.id);
                  const firstLine = requirement.spans[0]?.start_line ?? null;
                  setSelectedLine(firstLine);
                }
              }}
            >
              <div className="requirement-item-header">
                <div className="requirement-item-meta">
                  <span className="requirement-id">{requirement.id}</span>
                  <span
                    className="priority-chip"
                    style={{ backgroundColor: `${PRIORITY_COLORS[requirement.priority] ?? "#888"}20`, color: PRIORITY_COLORS[requirement.priority] ?? "#888" }}
                  >
                    <span
                      className="priority-dot"
                      style={{ backgroundColor: PRIORITY_COLORS[requirement.priority] ?? "#888" }}
                    />
                    {requirement.priority}
                  </span>
                  {requirement.text_span ? (
                    <span className="status-badge status-ok" title="Has text span">&#10003;</span>
                  ) : (
                    <span className="status-badge status-muted" title="No text span">&#10007;</span>
                  )}
                </div>
                {editingRequirementId !== requirement.id && (
                  <button
                    type="button"
                    className="edit-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(requirement);
                    }}
                    title="Edit requirement"
                  >
                    &#9998;
                  </button>
                )}
              </div>
              {editingRequirementId === requirement.id ? (
                <div className="edit-mode">
                  <textarea
                    className="w-full p-2 bg-[#171a1c] border border-[#99f7ff]/20 rounded text-[#eeeef0] text-xs resize-none"
                    rows={4}
                    value={editingText}
                    onChange={(e) => setEditingText(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="edit-actions">
                    <button
                      type="button"
                      className="btn-save"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSaveEdit();
                      }}
                      disabled={editingSaving}
                    >
                      {editingSaving ? "Saving..." : "Save"}
                    </button>
                    <button
                      type="button"
                      className="btn-cancel"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancelEdit();
                      }}
                      disabled={editingSaving}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <p className="requirement-text">{requirement.text}</p>
              )}
            </div>
          ))}
        </div>
        <h2>Graph Targets</h2>
        <GraphCanvas nodes={graphNodes} edges={graphEdges} activeNodeIds={activeNodeIds} />
      </div>
    </section>
  );
}
