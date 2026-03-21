import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import {
  getDocument,
  getEditorState,
  getStageOutputs,
  saveDocument,
  saveEditorState,
} from "../api/client";
import type { StageOutputsPayload } from "../types/models";

interface PipelineOutputsViewProps {
  stage: string;
}

const EDITABLE_NODES = new Set(["extract_understand", "match"]);
const EDITABLE_DOCUMENTS = new Map([
  ["nodes/generate_documents/proposed/cv.md", "cv"],
  ["nodes/generate_documents/proposed/motivation_letter.md", "motivation_letter"],
  ["nodes/generate_documents/proposed/application_email.md", "application_email"],
]);

export function PipelineOutputsView({ stage }: PipelineOutputsViewProps): JSX.Element {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [payload, setPayload] = useState<StageOutputsPayload | null>(null);
  const [error, setError] = useState("");
  const [selectedPath, setSelectedPath] = useState("");
  const [editorValue, setEditorValue] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");

  useEffect(() => {
    setSaveState("idle");
    getStageOutputs(source, jobId, stage)
      .then((data) => {
        setPayload(data);
        setError("");
        setSelectedPath(data.files[0]?.path ?? "");
      })
      .catch((err: Error) => {
        setError(err.message);
        setPayload(null);
      });
  }, [jobId, source, stage]);

  const selectedFile = useMemo(
    () => payload?.files.find((file) => file.path === selectedPath) ?? payload?.files[0] ?? null,
    [payload, selectedPath],
  );

  useEffect(() => {
    setEditorValue(selectedFile?.content ?? "");
  }, [selectedFile]);

  useEffect(() => {
    const requestedFile = searchParams.get("file");
    if (requestedFile) {
      setSelectedPath(requestedFile);
    }
  }, [searchParams]);

  const editableNode = payload?.node_name ?? null;
  const canEditJson =
    editableNode !== null && EDITABLE_NODES.has(editableNode) && selectedFile?.editable === true;
  const editableDocumentKey = selectedFile ? EDITABLE_DOCUMENTS.get(selectedFile.path) ?? null : null;
  const canEditDocument = editableDocumentKey !== null;

  const handleSave = async (): Promise<void> => {
    if (!editableNode) {
      return;
    }
    setSaveState("saving");
    setError("");
    try {
      const parsed = JSON.parse(editorValue) as Record<string, unknown>;
      await saveEditorState(source, jobId, editableNode, parsed);
      const refreshedEditor = await getEditorState(source, jobId, editableNode);
      const refreshedOutputs = await getStageOutputs(source, jobId, stage);
      setPayload(refreshedOutputs);
      setSelectedPath(refreshedOutputs.files[0]?.path ?? "");
      setEditorValue(JSON.stringify(refreshedEditor.state, null, 2));
      setSaveState("saved");
    } catch (err) {
      setSaveState("idle");
      setError(err instanceof Error ? err.message : "save failed");
    }
  };

  const handleSaveDocument = async (): Promise<void> => {
    if (!editableDocumentKey) {
      return;
    }
    setSaveState("saving");
    setError("");
    try {
      await saveDocument(source, jobId, editableDocumentKey, editorValue);
      const refreshedDocument = await getDocument(source, jobId, editableDocumentKey);
      const refreshedOutputs = await getStageOutputs(source, jobId, stage);
      setPayload(refreshedOutputs);
      setSelectedPath(
        refreshedOutputs.files.find((file) => file.path === selectedFile?.path)?.path ?? refreshedOutputs.files[0]?.path ?? "",
      );
      setEditorValue(refreshedDocument.content);
      setSaveState("saved");
    } catch (err) {
      setSaveState("idle");
      setError(err instanceof Error ? err.message : "save failed");
    }
  };

  return (
    <section className="panel split-grid">
      <div>
        <h2>Pipeline Outputs</h2>
        <p>Inspect local JSON/Markdown artifacts for the selected pipeline stage.</p>
        <p>
          Active stage: <strong>{stage}</strong>
        </p>
        {error ? <p className="error">{error}</p> : null}
        <div className="requirements-list">
          {(payload?.files ?? []).map((file) => (
            <button
              type="button"
              key={file.path}
              className={`requirement-item${file.path === selectedFile?.path ? " requirement-item-active" : ""}`}
              onClick={() => setSelectedPath(file.path)}
            >
              <strong>{file.path.split("/").slice(-2).join("/")}</strong>
              <span>{file.content_type}</span>
              <p>{file.path}</p>
            </button>
          ))}
          {!payload?.files.length ? <p>No local artifacts found for this stage yet.</p> : null}
        </div>
      </div>
      <div>
        <h2>{selectedFile?.path ?? "Artifact Preview"}</h2>
        {selectedFile?.content_type === "image" ? (
          <div className="stage-image-preview">
            <img src={selectedFile.content} alt={selectedFile.path} className="stage-image" />
          </div>
        ) : canEditJson ? (
          <>
            <textarea
              className="doc-preview stage-output-editor"
              value={editorValue}
              onChange={(event) => setEditorValue(event.target.value)}
            />
            <div className="pipeline-output-actions">
              <button type="button" className="view-tab view-tab-active" onClick={() => void handleSave()}>
              {saveState === "saving" ? "Saving..." : "Save JSON"}
            </button>
            {saveState === "saved" ? <span className="save-ok">Saved to local state.json</span> : null}
          </div>
          </>
        ) : canEditDocument ? (
          <>
            <textarea
              className="doc-preview stage-output-editor"
              value={editorValue}
              onChange={(event) => setEditorValue(event.target.value)}
            />
            <div className="pipeline-output-actions">
              <button type="button" className="view-tab view-tab-active" onClick={() => void handleSaveDocument()}>
                {saveState === "saving" ? "Saving..." : "Save document"}
              </button>
              {saveState === "saved" ? <span className="save-ok">Saved to local markdown</span> : null}
            </div>
          </>
        ) : (
          <textarea className="doc-preview stage-output-editor" value={selectedFile?.content ?? ""} readOnly />
        )}
      </div>
    </section>
  );
}
