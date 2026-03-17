import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { getViewTwoPayload } from "../api/client";
import { GraphCanvas } from "../components/GraphCanvas";
import type { RequirementItem, ViewTwoPayload } from "../types/models";

export function ViewTwoDocToGraph(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [payload, setPayload] = useState<ViewTwoPayload | null>(null);
  const [selectedRequirementId, setSelectedRequirementId] = useState<string>("");
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [error, setError] = useState<string>("");

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
        <div className="requirements-list">
          {(payload?.requirements ?? []).map((requirement) => (
            <button
              type="button"
              key={requirement.id}
              className={`requirement-item${
                requirement.id === selectedRequirementId ? " requirement-item-active" : ""
              }`}
              onClick={() => {
                setSelectedRequirementId(requirement.id);
                const firstLine = requirement.spans[0]?.start_line ?? null;
                setSelectedLine(firstLine);
              }}
            >
              <strong>{requirement.id}</strong>
              <span>{requirement.priority}</span>
              <p>{requirement.text}</p>
            </button>
          ))}
        </div>
        <h2>Graph Targets</h2>
        <GraphCanvas nodes={graphNodes} edges={graphEdges} activeNodeIds={activeNodeIds} />
      </div>
    </section>
  );
}
