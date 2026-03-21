import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { getViewOnePayload, getViewThreePayload, saveDocument } from "../api/client";
import { GraphCanvas } from "../components/GraphCanvas";
import type { ViewOnePayload, ViewThreePayload } from "../types/models";

type DocKey = "cv" | "motivation_letter" | "application_email";

interface LineDiff {
  lineNum: number;
  proposed: string;
  approved: string | null;
  status: "same" | "added" | "removed" | "changed";
}

function computeLineDiff(proposedLines: string[], approvedLines: string[]): LineDiff[] {
  const maxLen = Math.max(proposedLines.length, approvedLines.length);
  const result: LineDiff[] = [];

  for (let i = 0; i < maxLen; i++) {
    const proposedLine = proposedLines[i] ?? null;
    const approvedLine = approvedLines[i] ?? null;

    if (proposedLine === null) {
      result.push({ lineNum: i + 1, proposed: "", approved: approvedLine, status: "removed" });
    } else if (approvedLine === null) {
      result.push({ lineNum: i + 1, proposed: proposedLine, approved: null, status: "added" });
    } else if (proposedLine === approvedLine) {
      result.push({ lineNum: i + 1, proposed: proposedLine, approved: approvedLine, status: "same" });
    } else {
      result.push({ lineNum: i + 1, proposed: proposedLine, approved: approvedLine, status: "changed" });
    }
  }

  return result;
}

function countWords(text: string): number {
  return text.trim().split(/\s+/).filter((w) => w.length > 0).length;
}

export function ViewThreeGraphToDoc(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [payload, setPayload] = useState<ViewThreePayload | null>(null);
  const [viewOnePayload, setViewOnePayload] = useState<ViewOnePayload | null>(null);
  const [activeDoc, setActiveDoc] = useState<DocKey>("motivation_letter");
  const [editContent, setEditContent] = useState<string>("");
  const [showDiff, setShowDiff] = useState<boolean>(false);
  const [approvedContent, setApprovedContent] = useState<string>("");
  const [approvedLoading, setApprovedLoading] = useState<boolean>(false);
  const [approvedError, setApprovedError] = useState<string>("");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string>("");
  const [error, setError] = useState("");

  useEffect(() => {
    getViewThreePayload(source, jobId)
      .then(setPayload)
      .catch((err: Error) => setError(err.message));
  }, [source, jobId]);

  useEffect(() => {
    getViewOnePayload(source, jobId)
      .then(setViewOnePayload)
      .catch(() => {
        // Silently fail - match data may not be available
      });
  }, [source, jobId]);

  useEffect(() => {
    if (!payload) return;
    setEditContent(payload.documents[activeDoc] ?? "");
  }, [payload, activeDoc]);

  useEffect(() => {
    if (!showDiff) return;
    setApprovedLoading(true);
    setApprovedError("");
    fetch(`/api/v1/jobs/${source}/${jobId}/documents/${activeDoc}/approved`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.text();
      })
      .then((text) => {
        setApprovedContent(text);
        setApprovedLoading(false);
      })
      .catch((err: Error) => {
        setApprovedError(err.message);
        setApprovedLoading(false);
      });
  }, [source, jobId, activeDoc, showDiff]);

  const confidenceScore = useMemo<number | null>(() => {
    if (!viewOnePayload?.edges) return null;
    const matchEdges = viewOnePayload.edges.filter((e) => e.score !== null && e.score > 0);
    if (matchEdges.length === 0) return null;
    const total = matchEdges.reduce((sum, e) => sum + (e.score ?? 0), 0);
    return Math.round((total / matchEdges.length) * 100) / 100;
  }, [viewOnePayload]);

  const wordCount = useMemo(() => countWords(editContent), [editContent]);
  const charCount = useMemo(() => editContent.length, [editContent]);

  const diffLines = useMemo<LineDiff[] | null>(() => {
    if (!showDiff || approvedLoading || approvedError) return null;
    const proposedLines = editContent.split("\n");
    const approvedLines = approvedContent.split("\n");
    return computeLineDiff(proposedLines, approvedLines);
  }, [showDiff, editContent, approvedContent, approvedLoading, approvedError]);

  const handleSave = async (): Promise<void> => {
    setSaveStatus("saving");
    setSaveError("");
    try {
      await saveDocument(source, jobId, activeDoc, editContent);
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
      setSaveStatus("error");
    }
  };

  const nodes = payload?.nodes.map((node) => ({ id: node.id, label: node.label })) ?? [];
  const edges =
    payload?.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      label: edge.score !== null ? `${edge.label} (${edge.score.toFixed(2)})` : edge.label,
    })) ?? [];

  return (
    <section className="panel split-grid">
      <div>
        <h2>View 3: Graph to Document</h2>
        <p>Inspect generated content and annotate redaction decisions.</p>
        {error ? <p className="error">{error}</p> : null}
        <div className="doc-tabs">
          <button
            type="button"
            className={activeDoc === "motivation_letter" ? "doc-tab doc-tab-active" : "doc-tab"}
            onClick={() => setActiveDoc("motivation_letter")}
          >
            Motivation
          </button>
          <button
            type="button"
            className={activeDoc === "cv" ? "doc-tab doc-tab-active" : "doc-tab"}
            onClick={() => setActiveDoc("cv")}
          >
            CV
          </button>
          <button
            type="button"
            className={activeDoc === "application_email" ? "doc-tab doc-tab-active" : "doc-tab"}
            onClick={() => setActiveDoc("application_email")}
          >
            Email
          </button>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            className={showDiff ? "doc-tab doc-tab-active" : "doc-tab"}
            onClick={() => setShowDiff(!showDiff)}
          >
            {showDiff ? "Hide Diff" : "Show Diff"}
          </button>
          <button
            type="button"
            className="doc-tab"
            onClick={handleSave}
            disabled={saveStatus === "saving"}
          >
            {saveStatus === "saving" ? "Saving..." : "Save"}
          </button>
          {saveStatus === "saved" && <span className="save-ok">Saved!</span>}
          {saveStatus === "error" && <span className="error">{saveError}</span>}
          {confidenceScore !== null && (
            <span style={{ marginLeft: "auto", fontSize: "13px", color: "var(--text-dim)" }}>
              Match confidence: <strong>{confidenceScore.toFixed(2)}</strong>
            </span>
          )}
        </div>

        {showDiff ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            <div>
              <h4 style={{ margin: "0 0 6px", fontSize: "13px" }}>Proposed</h4>
              <div
                style={{
                  border: "1px solid var(--line)",
                  borderRadius: "12px",
                  padding: "8px",
                  minHeight: "280px",
                  maxHeight: "400px",
                  overflow: "auto",
                  background: "#fff",
                }}
              >
                {diffLines?.map((diff) => (
                  <div
                    key={diff.lineNum}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "40px 1fr",
                      gap: "6px",
                      padding: "2px 4px",
                      background:
                        diff.status === "added" || diff.status === "changed"
                          ? "#fef9c3"
                          : diff.status === "removed"
                          ? "#fee2e2"
                          : "transparent",
                      fontFamily: "monospace",
                      fontSize: "12px",
                      lineHeight: "1.4",
                    }}
                  >
                    <span style={{ color: "var(--text-dim)", textAlign: "right" }}>{diff.lineNum}</span>
                    <span style={{ whiteSpace: "pre-wrap" }}>{diff.proposed || "(empty)"}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 style={{ margin: "0 0 6px", fontSize: "13px" }}>Approved</h4>
              {approvedLoading ? (
                <div style={{ padding: "12px", color: "var(--text-dim)" }}>Loading...</div>
              ) : approvedError ? (
                <div style={{ padding: "12px", color: "var(--bad)" }}>{approvedError}</div>
              ) : (
                <div
                  style={{
                    border: "1px solid var(--line)",
                    borderRadius: "12px",
                    padding: "8px",
                    minHeight: "280px",
                    maxHeight: "400px",
                    overflow: "auto",
                    background: "#f8f8f8",
                  }}
                >
                  {diffLines?.map((diff) => (
                    <div
                      key={diff.lineNum}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "40px 1fr",
                        gap: "6px",
                        padding: "2px 4px",
                        background:
                          diff.status === "removed" || diff.status === "changed"
                            ? "#fce7f3"
                            : "transparent",
                        fontFamily: "monospace",
                        fontSize: "12px",
                        lineHeight: "1.4",
                      }}
                    >
                      <span style={{ color: "var(--text-dim)", textAlign: "right" }}>{diff.lineNum}</span>
                      <span style={{ whiteSpace: "pre-wrap" }}>{diff.approved ?? "(not present)"}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <textarea
            className="doc-preview"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
          />
        )}

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: "6px",
            fontSize: "12px",
            color: "var(--text-dim)",
          }}
        >
          <span>{wordCount} words</span>
          <span>{charCount} characters</span>
        </div>
      </div>
      <div>
        <h2>Contributing Graph Nodes</h2>
        <GraphCanvas nodes={nodes} edges={edges} />
      </div>
    </section>
  );
}
