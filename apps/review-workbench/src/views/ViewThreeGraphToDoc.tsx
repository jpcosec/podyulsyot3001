import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { getViewThreePayload } from "../api/client";
import { GraphCanvas } from "../components/GraphCanvas";
import type { ViewThreePayload } from "../types/models";

type DocKey = "cv" | "motivation_letter" | "application_email";

export function ViewThreeGraphToDoc(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [payload, setPayload] = useState<ViewThreePayload | null>(null);
  const [activeDoc, setActiveDoc] = useState<DocKey>("motivation_letter");
  const [error, setError] = useState("");

  useEffect(() => {
    getViewThreePayload(source, jobId)
      .then(setPayload)
      .catch((err: Error) => setError(err.message));
  }, [source, jobId]);

  const documentText = useMemo(() => {
    if (!payload) {
      return "";
    }
    return payload.documents[activeDoc] ?? "";
  }, [payload, activeDoc]);

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
        <textarea className="doc-preview" value={documentText} readOnly />
      </div>
      <div>
        <h2>Contributing Graph Nodes</h2>
        <GraphCanvas nodes={nodes} edges={edges} />
      </div>
    </section>
  );
}
