import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { StageStatusBadge } from "../components/StageStatusBadge";
import { getJobTimeline } from "../api/client";
import type { JobTimeline } from "../types/models";
import { ViewOneGraphExplorer } from "../views/ViewOneGraphExplorer";
import { ViewThreeGraphToDoc } from "../views/ViewThreeGraphToDoc";
import { ViewTwoDocToGraph } from "../views/ViewTwoDocToGraph";

type ViewKey = "view-1" | "view-2" | "view-3";

export function JobStagePage(): JSX.Element {
  const params = useParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";
  const [timeline, setTimeline] = useState<JobTimeline | null>(null);
  const [error, setError] = useState<string>("");
  const [activeView, setActiveView] = useState<ViewKey>("view-2");

  useEffect(() => {
    getJobTimeline(source, jobId)
      .then(setTimeline)
      .catch((err: Error) => setError(err.message));
  }, [source, jobId]);

  const view = useMemo<ViewKey>(() => {
    if (!timeline) {
      return "view-2";
    }
    if (timeline.current_node.includes("match") || timeline.current_node.includes("review")) {
      return "view-1";
    }
    if (timeline.current_node.includes("generate") || timeline.current_node.includes("render")) {
      return "view-3";
    }
    return "view-2";
  }, [timeline]);

  useEffect(() => {
    setActiveView(view);
  }, [view]);

  return (
    <section className="panel">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <span>
          {source} {jobId}
        </span>
      </div>
      <h1>
        Job {jobId} ({source})
      </h1>
      {error ? <p className="error">{error}</p> : null}
      {timeline ? (
        <>
          <p>
            Current node: <strong>{timeline.current_node}</strong>
          </p>
          <div className="stage-list">
            {timeline.stages.map((stage) => (
              <div key={stage.stage} className="stage-item">
                <span>{stage.stage}</span>
                <StageStatusBadge status={stage.status} />
              </div>
            ))}
          </div>
          <div className="view-tabs">
            <button
              type="button"
              className={activeView === "view-1" ? "view-tab view-tab-active" : "view-tab"}
              onClick={() => setActiveView("view-1")}
            >
              View 1 Graph Explorer
            </button>
            <button
              type="button"
              className={activeView === "view-2" ? "view-tab view-tab-active" : "view-tab"}
              onClick={() => setActiveView("view-2")}
            >
              View 2 Document to Graph
            </button>
            <button
              type="button"
              className={activeView === "view-3" ? "view-tab view-tab-active" : "view-tab"}
              onClick={() => setActiveView("view-3")}
            >
              View 3 Graph to Document
            </button>
          </div>
        </>
      ) : (
        <p>Loading job timeline...</p>
      )}
      {activeView === "view-1" ? <ViewOneGraphExplorer /> : null}
      {activeView === "view-2" ? <ViewTwoDocToGraph /> : null}
      {activeView === "view-3" ? <ViewThreeGraphToDoc /> : null}
    </section>
  );
}
