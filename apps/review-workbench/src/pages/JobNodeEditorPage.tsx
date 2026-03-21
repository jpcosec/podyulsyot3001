import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { getEditorState, saveEditorState } from "../api/client";

type EditorStage = "extract_understand" | "match";

type FlowNodeData = {
  label: string;
  path: string;
};

type FlowNode = Node<FlowNodeData>;
type FlowEdge = Edge;

const STAGE_OPTIONS: Array<{ key: EditorStage; label: string }> = [
  { key: "extract_understand", label: "Extract" },
  { key: "match", label: "Match" },
];

export function JobNodeEditorPage(): JSX.Element {
  return (
    <ReactFlowProvider>
      <JobNodeEditorInner />
    </ReactFlowProvider>
  );
}

function JobNodeEditorInner(): JSX.Element {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [stage, setStage] = useState<EditorStage>("extract_understand");
  const [statePayload, setStatePayload] = useState<Record<string, unknown> | null>(null);
  const [selectedPath, setSelectedPath] = useState<string>("$");
  const [editorValue, setEditorValue] = useState<string>("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const requestedStage = searchParams.get("stage");
    if (requestedStage === "extract_understand" || requestedStage === "match") {
      setStage(requestedStage);
    }
  }, [searchParams]);

  useEffect(() => {
    getEditorState(source, jobId, stage)
      .then((payload) => {
        setStatePayload(payload.state);
        setSelectedPath("$");
        setError("");
        setSaveState("idle");
      })
      .catch((err: Error) => {
        setStatePayload(null);
        setError(err.message);
      });
  }, [jobId, source, stage]);

  const graph = useMemo(() => buildGraph(stage, statePayload), [stage, statePayload]);
  const selectedValue = useMemo(() => getValueAtPath(statePayload, selectedPath), [selectedPath, statePayload]);

  useEffect(() => {
    setEditorValue(toPrettyJson(selectedValue));
  }, [selectedValue]);

  const handleSave = async (): Promise<void> => {
    if (!statePayload) {
      return;
    }
    setSaveState("saving");
    setError("");
    try {
      const parsed = JSON.parse(editorValue) as unknown;
      const nextState = setValueAtPath(statePayload, selectedPath, parsed);
      const payload = await saveEditorState(source, jobId, stage, nextState as Record<string, unknown>);
      setStatePayload(payload.state);
      setSaveState("saved");
    } catch (err) {
      setSaveState("idle");
      setError(err instanceof Error ? err.message : "save failed");
    }
  };

  return (
    <section className="panel node-editor-page">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to={`/jobs/${source}/${jobId}`}>{source} {jobId}</Link>
        <span>/</span>
        <span>node editor</span>
      </div>
      <div className="node-editor-header">
        <div>
          <h1>Job Node Editor</h1>
          <p>Edit local JSON-backed graph data for the current job.</p>
        </div>
        <div className="view-tabs">
          {STAGE_OPTIONS.map((option) => (
            <button
              key={option.key}
              type="button"
              className={stage === option.key ? "view-tab view-tab-active" : "view-tab"}
              onClick={() => setStage(option.key)}
            >
              {option.label}
            </button>
          ))}
          <Link className="view-tab" to={`/jobs/${source}/${jobId}`}>Back to job</Link>
        </div>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <div className="node-editor-grid">
        <div className="node-editor-canvas">
          <ReactFlow
            nodes={graph.nodes}
            edges={graph.edges}
            fitView
            onNodeClick={(_event, node) => setSelectedPath(node.data.path)}
          >
            <MiniMap pannable zoomable />
            <Controls />
            <Background gap={20} size={1} />
          </ReactFlow>
        </div>
        <div className="node-editor-sidebar">
          <h2>Selection</h2>
          <p>
            Path: <code>{selectedPath}</code>
          </p>
          <textarea
            className="doc-preview stage-output-editor"
            value={editorValue}
            onChange={(event) => setEditorValue(event.target.value)}
          />
          <div className="pipeline-output-actions">
            <button type="button" className="view-tab view-tab-active" onClick={() => void handleSave()}>
              {saveState === "saving" ? "Saving..." : "Save selection"}
            </button>
            {saveState === "saved" ? <span className="save-ok">Saved to local state.json</span> : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function buildGraph(stage: EditorStage, payload: Record<string, unknown> | null): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];

  pushNode(nodes, "$", stage === "extract_understand" ? "Extract Job" : "Match Graph", "$");

  if (!payload) {
    return { nodes, edges };
  }

  if (stage === "extract_understand") {
    buildExtractGraph(payload, nodes, edges);
  } else {
    buildMatchGraph(payload, nodes, edges);
  }
  return layoutGraph(nodes, edges);
}

function buildExtractGraph(payload: Record<string, unknown>, nodes: FlowNode[], edges: FlowEdge[]): void {
  const requirements = Array.isArray(payload.requirements) ? payload.requirements : [];
  const constraints = Array.isArray(payload.constraints) ? payload.constraints : [];
  const risks = Array.isArray(payload.risk_areas) ? payload.risk_areas : [];
  const contactInfo = isRecord(payload.contact_info) ? payload.contact_info : null;
  const salaryGrade = typeof payload.salary_grade === "string" ? payload.salary_grade : null;

  requirements.forEach((item, index) => {
    const record = isRecord(item) ? item : {};
    const id = typeof record.id === "string" ? record.id : `REQ-${index + 1}`;
    const text = typeof record.text === "string" ? record.text : id;
    const nodeId = `req-${index}`;
    pushNode(nodes, nodeId, `${id}: ${text}`, `$.requirements[${index}]`);
    pushEdge(edges, `$`, nodeId, "REQUIRES");
  });

  constraints.forEach((item, index) => {
    const record = isRecord(item) ? item : {};
    const kind = typeof record.constraint_type === "string" ? record.constraint_type : `constraint-${index + 1}`;
    const text = typeof record.description === "string" ? record.description : kind;
    const nodeId = `constraint-${index}`;
    pushNode(nodes, nodeId, `${kind}: ${text}`, `$.constraints[${index}]`);
    pushEdge(edges, `$`, nodeId, "CONSTRAINS");
  });

  risks.forEach((item, index) => {
    const label = typeof item === "string" ? item : `risk-${index + 1}`;
    const nodeId = `risk-${index}`;
    pushNode(nodes, nodeId, label, `$.risk_areas[${index}]`);
    pushEdge(edges, `$`, nodeId, "RISK");
  });

  if (contactInfo) {
    pushNode(nodes, "contact", formatContactLabel(contactInfo), "$.contact_info");
    pushEdge(edges, "$", "contact", "CONTACT");
  }

  if (salaryGrade) {
    pushNode(nodes, "salary", salaryGrade, "$.salary_grade");
    pushEdge(edges, "$", "salary", "SALARY");
  }
}

function buildMatchGraph(payload: Record<string, unknown>, nodes: FlowNode[], edges: FlowEdge[]): void {
  const requirements = Array.isArray(payload.requirements) ? payload.requirements : [];
  const matches = Array.isArray(payload.matches) ? payload.matches : [];
  const requirementNodeIds = new Map<string, string>();

  requirements.forEach((item, index) => {
    const record = isRecord(item) ? item : {};
    const id = typeof record.id === "string" ? record.id : `REQ-${index + 1}`;
    const text = typeof record.text === "string" ? record.text : id;
    const nodeId = `req-${index}`;
    requirementNodeIds.set(id, nodeId);
    pushNode(nodes, nodeId, `${id}: ${text}`, `$.requirements[${index}]`);
    pushEdge(edges, "$", nodeId, "REQUIREMENT");
  });

  matches.forEach((item, index) => {
    const record = isRecord(item) ? item : {};
    const reqId = typeof record.req_id === "string" ? record.req_id : `REQ-${index + 1}`;
    const evidenceId = typeof record.evidence_id === "string" ? record.evidence_id : `evidence-${index + 1}`;
    const score = typeof record.match_score === "number" ? record.match_score.toFixed(2) : "n/a";
    const matchNodeId = `match-${index}`;
    const evidenceNodeId = `evidence-${index}`;

    if (!requirementNodeIds.has(reqId)) {
      const fallbackReqNodeId = `req-fallback-${index}`;
      requirementNodeIds.set(reqId, fallbackReqNodeId);
      pushNode(nodes, fallbackReqNodeId, reqId, `$.matches[${index}].req_id`);
      pushEdge(edges, "$", fallbackReqNodeId, "REQUIREMENT");
    }

    pushNode(nodes, matchNodeId, `Match ${reqId} (${score})`, `$.matches[${index}]`);
    pushNode(nodes, evidenceNodeId, evidenceId, `$.matches[${index}].evidence_id`);
    pushEdge(edges, requirementNodeIds.get(reqId) ?? "$", matchNodeId, "MATCHED_BY");
    pushEdge(edges, matchNodeId, evidenceNodeId, "SUPPORTED_BY");
  });
}

function pushNode(nodes: FlowNode[], id: string, label: string, path: string): void {
  nodes.push({
    id,
    position: { x: 0, y: 0 },
    data: { label, path },
    style: {
      border: "1px solid #123c69",
      borderRadius: 12,
      padding: 10,
      width: 220,
      background: "#fffdf9",
      color: "#1f2933",
      fontSize: 12,
    },
  });
}

function pushEdge(edges: FlowEdge[], source: string, target: string, label: string): void {
  edges.push({
    id: `${source}-${target}-${label}`,
    source,
    target,
    label,
    markerEnd: { type: MarkerType.ArrowClosed },
  });
}

function layoutGraph(nodes: FlowNode[], edges: FlowEdge[]): { nodes: FlowNode[]; edges: FlowEdge[] } {
  return {
    nodes: nodes.map((node, index) => ({
      ...node,
      position: {
        x: (index % 3) * 260,
        y: Math.floor(index / 3) * 140,
      },
    })),
    edges,
  };
}

function formatContactLabel(contactInfo: Record<string, unknown>): string {
  const name = typeof contactInfo.name === "string" ? contactInfo.name : "Unknown contact";
  const email = typeof contactInfo.email === "string" ? contactInfo.email : "no-email";
  return `${name}\n${email}`;
}

function getValueAtPath(value: unknown, path: string): unknown {
  if (path === "$" || !path) {
    return value;
  }
  const segments = tokenizePath(path);
  let current = value;
  for (const segment of segments) {
    if (typeof segment === "number") {
      if (!Array.isArray(current)) {
        return null;
      }
      current = current[segment];
    } else {
      if (!isRecord(current)) {
        return null;
      }
      current = current[segment];
    }
  }
  return current;
}

function setValueAtPath(root: unknown, path: string, nextValue: unknown): unknown {
  if (path === "$" || !path) {
    return nextValue;
  }
  const segments = tokenizePath(path);
  return applyPathUpdate(root, segments, nextValue);
}

function applyPathUpdate(current: unknown, segments: Array<string | number>, nextValue: unknown): unknown {
  if (segments.length === 0) {
    return nextValue;
  }
  const [head, ...rest] = segments;
  if (typeof head === "number") {
    const source = Array.isArray(current) ? [...current] : [];
    source[head] = applyPathUpdate(source[head], rest, nextValue);
    return source;
  }
  const source = isRecord(current) ? { ...current } : {};
  source[head] = applyPathUpdate(source[head], rest, nextValue);
  return source;
}

function tokenizePath(path: string): Array<string | number> {
  return path
    .replace(/^\$\.?/, "")
    .split(".")
    .flatMap((segment) => {
      const output: Array<string | number> = [];
      const match = segment.match(/^([^[]+)(.*)$/);
      if (!match) {
        return output;
      }
      output.push(match[1]);
      const indexes = match[2].match(/\[(\d+)\]/g) ?? [];
      indexes.forEach((indexToken) => {
        output.push(Number(indexToken.replace(/[^0-9]/g, "")));
      });
      return output;
    })
    .filter((segment) => segment !== "");
}

function toPrettyJson(value: unknown): string {
  return JSON.stringify(value ?? null, null, 2);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
