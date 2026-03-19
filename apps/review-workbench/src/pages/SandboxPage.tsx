import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { GraphCanvas } from "../components/GraphCanvas";
import { JobTree } from "../components/JobTree";
import { StageStatusBadge } from "../components/StageStatusBadge";
import type {
  GraphEdge,
  GraphNode,
  JobListItem,
  RequirementItem,
  StageStatus,
} from "../types/models";

type DocKey = "motivation_letter" | "cv" | "application_email";

const MOCK_JOBS: JobListItem[] = [
  {
    source: "tu_berlin",
    job_id: "201637",
    thread_id: "tu_berlin_201637",
    current_node: "review_match",
    status: "paused_review",
    updated_at: "2026-03-17T09:13:00Z",
  },
  {
    source: "linkedin",
    job_id: "lk_87421",
    thread_id: "linkedin_lk_87421",
    current_node: "extract_understand",
    status: "running",
    updated_at: "2026-03-17T08:04:00Z",
  },
  {
    source: "indeed",
    job_id: "id_55190",
    thread_id: "indeed_id_55190",
    current_node: "package",
    status: "completed",
    updated_at: "2026-03-16T22:50:00Z",
  },
];

const MOCK_SOURCE_LINES = [
  "Faculty IV - Electrical Engineering and Computer Science",
  "Research Assistant (PhD candidate) in Data Integration and Data Preparation",
  "Your profile: Master degree in Computer Science or related field",
  "Required: strong SQL and distributed systems knowledge",
  "Application deadline: 27.03.2026",
  "Contact: Prof. Dr. Abedjan (sekr@d2ip.tu-berlin.de)",
];

const MOCK_REQUIREMENTS: RequirementItem[] = [
  {
    id: "R1",
    text: "Master's degree in Computer Science or related field",
    priority: "must",
    spans: [{ requirement_id: "R1", start_line: 3, end_line: 3, text_preview: "Master degree" }],
  },
  {
    id: "R2",
    text: "Strong SQL knowledge",
    priority: "must",
    spans: [{ requirement_id: "R2", start_line: 4, end_line: 4, text_preview: "SQL" }],
  },
  {
    id: "R3",
    text: "Distributed systems experience",
    priority: "nice",
    spans: [{ requirement_id: "R3", start_line: 4, end_line: 4, text_preview: "distributed systems" }],
  },
];

const MOCK_VIEW1_NODES: GraphNode[] = [
  { id: "profile", label: "Profile", kind: "profile" },
  { id: "job", label: "Job Posting", kind: "job" },
  { id: "R1", label: "Requirement R1", kind: "requirement" },
  { id: "R2", label: "Requirement R2", kind: "requirement" },
  { id: "E12", label: "Evidence E12", kind: "evidence" },
  { id: "E23", label: "Evidence E23", kind: "evidence" },
];

const MOCK_VIEW1_EDGES: GraphEdge[] = [
  {
    source: "job",
    target: "R1",
    label: "HAS_REQUIREMENT",
    score: null,
    reasoning: null,
    evidence_id: null,
  },
  {
    source: "job",
    target: "R2",
    label: "HAS_REQUIREMENT",
    score: null,
    reasoning: null,
    evidence_id: null,
  },
  {
    source: "E12",
    target: "R1",
    label: "MATCHED_BY",
    score: 0.92,
    reasoning: "Degree and thesis domain align strongly with requirement.",
    evidence_id: "P_EDU_001",
  },
  {
    source: "E23",
    target: "R2",
    label: "MATCHED_BY",
    score: 0.83,
    reasoning: "Project achievements explicitly mention advanced SQL work.",
    evidence_id: "P_EXP_014",
  },
  {
    source: "profile",
    target: "E12",
    label: "HAS_EVIDENCE",
    score: null,
    reasoning: null,
    evidence_id: null,
  },
  {
    source: "profile",
    target: "E23",
    label: "HAS_EVIDENCE",
    score: null,
    reasoning: null,
    evidence_id: null,
  },
];

const MOCK_DOCS: Record<DocKey, string> = {
  motivation_letter:
    "Dear Prof. Dr. Abedjan,\n\nI am applying for the Research Assistant position in Data Integration and Data Preparation...",
  cv: "SUMMARY\nData engineer and researcher with experience in SQL, distributed systems, and machine learning...",
  application_email:
    "Subject: Application IV-81/26\n\nDear Prof. Dr. Abedjan,\nPlease find my application attached...",
};

export function SandboxPage(): JSX.Element {
  const [selectedRequirementId, setSelectedRequirementId] = useState<string>(
    MOCK_REQUIREMENTS[0]?.id ?? "",
  );
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [activeDoc, setActiveDoc] = useState<DocKey>("motivation_letter");

  const selectedRequirement = useMemo(
    () => MOCK_REQUIREMENTS.find((item) => item.id === selectedRequirementId) ?? null,
    [selectedRequirementId],
  );

  const highlightedLines = useMemo(() => {
    return new Set(
      selectedRequirement?.spans.flatMap((span) => {
        const output: number[] = [];
        for (let line = span.start_line; line <= span.end_line; line += 1) {
          output.push(line);
        }
        return output;
      }) ?? [],
    );
  }, [selectedRequirement]);

  const statusList: StageStatus[] = [
    "pending",
    "running",
    "paused_review",
    "completed",
    "failed",
  ];

  const view2Nodes = [
    { id: "source", label: "Source", kind: "source" },
    ...MOCK_REQUIREMENTS.map((req) => ({ id: req.id, label: req.id, kind: "requirement" })),
  ];
  const view2Edges = MOCK_REQUIREMENTS.map((req) => ({
    source: "source",
    target: req.id,
    label: req.priority,
  }));

  const activeGraphNodeIds = selectedRequirement ? [selectedRequirement.id] : [];

  return (
    <section className="panel">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <span>Sandbox</span>
      </div>
      <h1>Component Sandbox</h1>
      <p>Isolated frontend components with fake data, no API calls.</p>

      <div className="sandbox-grid">
        <article className="panel sandbox-card">
          <h2>StageStatusBadge</h2>
          <div className="sandbox-badge-row">
            {statusList.map((status) => (
              <StageStatusBadge key={status} status={status} />
            ))}
          </div>
        </article>

        <article className="panel sandbox-card">
          <h2>JobTree</h2>
          <JobTree jobs={MOCK_JOBS} />
        </article>

        <article className="panel sandbox-card">
          <h2>GraphCanvas</h2>
          <GraphCanvas
            nodes={MOCK_VIEW1_NODES.map((node) => ({ id: node.id, label: node.label }))}
            edges={MOCK_VIEW1_EDGES.map((edge) => ({
              source: edge.source,
              target: edge.target,
              label: edge.score ? `${edge.label} (${edge.score.toFixed(2)})` : edge.label,
            }))}
            activeNodeIds={activeGraphNodeIds}
          />
        </article>

        <article className="panel sandbox-card">
          <h2>Text Tagger</h2>
          <p>
            Open the dedicated route for text highlighting and node cards without extra sandbox
            noise.
          </p>
          <p>
            <Link to="/sandbox/text_tagger">Go to text tagger</Link>
          </p>
        </article>

        <article className="panel sandbox-card">
          <h2>CV Graph Editor</h2>
          <p>
            Open the deterministic base-CV graph editor powered by React Flow and the existing
            profile data.
          </p>
          <p>
            <Link to="/sandbox/cv_graph">Go to CV graph editor</Link>
          </p>
        </article>

        <article className="panel sandbox-card">
          <h2>Node Editor Plan</h2>
          <p>
            Implementation plan for the node-to-node editor phase with state machine, overlays,
            typed modal forms, and acceptance criteria.
          </p>
          <p>
            <Link to="/sandbox/node_editor_plan">Go to node editor plan</Link>
          </p>
        </article>
      </div>

      <h2>Mock View 2: Document to Graph</h2>
      <section className="panel split-grid">
        <div>
          <h3>Source</h3>
          <div className="source-doc">
            {MOCK_SOURCE_LINES.map((line, index) => {
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
                  onClick={() => {
                    setSelectedLine(lineNumber);
                    const linked = MOCK_REQUIREMENTS.find((requirement) =>
                      requirement.spans.some(
                        (span) => lineNumber >= span.start_line && lineNumber <= span.end_line,
                      ),
                    );
                    if (linked) {
                      setSelectedRequirementId(linked.id);
                    }
                  }}
                >
                  <span className="source-line-no">{lineNumber}</span>
                  <span className="source-line-text">{line}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div>
          <h3>Requirements</h3>
          <div className="requirements-list">
            {MOCK_REQUIREMENTS.map((requirement) => (
              <button
                type="button"
                key={requirement.id}
                className={`requirement-item${
                  requirement.id === selectedRequirementId ? " requirement-item-active" : ""
                }`}
                onClick={() => {
                  setSelectedRequirementId(requirement.id);
                  setSelectedLine(requirement.spans[0]?.start_line ?? null);
                }}
              >
                <strong>{requirement.id}</strong>
                <span>{requirement.priority}</span>
                <p>{requirement.text}</p>
              </button>
            ))}
          </div>
          <GraphCanvas
            nodes={view2Nodes.map((node) => ({ id: node.id, label: node.label }))}
            edges={view2Edges}
            activeNodeIds={activeGraphNodeIds}
          />
        </div>
      </section>

      <h2>Mock View 3: Graph to Document</h2>
      <section className="panel split-grid">
        <div>
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
          <textarea className="doc-preview" value={MOCK_DOCS[activeDoc]} readOnly />
        </div>
        <div>
          <GraphCanvas
            nodes={MOCK_VIEW1_NODES.map((node) => ({ id: node.id, label: node.label }))}
            edges={MOCK_VIEW1_EDGES.map((edge) => ({
              source: edge.source,
              target: edge.target,
              label: edge.score ? `${edge.label} (${edge.score.toFixed(2)})` : edge.label,
            }))}
          />
        </div>
      </section>
    </section>
  );
}
