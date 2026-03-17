import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { getViewOnePayload } from "../api/client";
import { GraphCanvas } from "../components/GraphCanvas";
import type { ViewOnePayload } from "../types/models";

export function ViewOneGraphExplorer(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [payload, setPayload] = useState<ViewOnePayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getViewOnePayload(source, jobId)
      .then(setPayload)
      .catch((err: Error) => setError(err.message));
  }, [source, jobId]);

  const nodes = payload?.nodes.map((node) => ({ id: node.id, label: node.label })) ?? [];
  const edges =
    payload?.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      label: edge.score !== null ? `${edge.label} (${edge.score.toFixed(2)})` : edge.label,
    })) ?? [];

  return (
    <section className="panel">
      <h2>View 1: Graph Explorer</h2>
      <p>Inspect profile-job-match links and review graph relationships.</p>
      {error ? <p className="error">{error}</p> : null}
      <GraphCanvas nodes={nodes} edges={edges} />
      <div className="match-table">
        {(payload?.edges ?? [])
          .filter((edge) => edge.label === "MATCHED_BY")
          .map((edge, index) => (
            <article key={`${edge.source}-${edge.target}-${index}`} className="match-row">
              <strong>
                {edge.source}
                {" -> "}
                {edge.target}
              </strong>
              <span>Score: {edge.score ?? 0}</span>
              <p>{edge.reasoning ?? "No reasoning available."}</p>
            </article>
          ))}
      </div>
    </section>
  );
}
