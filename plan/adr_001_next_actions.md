# ADR-001 Next Actions

Forward-looking action plan derived from `plan/adr_001_execution_tracker.md`.
Focuses on what to do next to unblock each phase, in priority order.

Last updated: 2026-03-17

---

## Critical Path

Phase 0 blocks everything else. Within Phase 0, the data migration scripts (0.7, 0.8)
are the highest-priority items because all three views currently read from filesystem
artifacts — migrating to Neo4j-backed data is the prerequisite for all interactive
features (node editing, comments, review decisions).

```
Phase 0 (complete foundation)
  └─> Phase 1 (Doc-to-Graph editing)
  └─> Phase 2 (Graph Explorer mutations)
  └─> Phase 3 (Graph-to-Doc Slate editing)
      └─> Phase 4 (dashboard, filtering)
          └─> Phase 5 (LangChain migration)
              └─> Phase 6 (multi-source scale)
```

Phases 1-3 can be parallelized once Phase 0 is complete. Phase 4 depends on
the data being in Neo4j (cross-job queries). Phase 5 is independent of UI work
but benefits from Neo4j being the data plane.

---

## Immediate: Complete Phase 0

### Action 0.A — Install missing pip dependencies

```bash
conda activate phd2  # or whatever the env is
pip install fastapi uvicorn neo4j
```

Validates: `python -c "import fastapi; import neo4j; print('ok')"`

### Action 0.B — Start Neo4j and verify

```bash
docker compose -f docker-compose.neo4j.yml up -d
python -m src.cli.bootstrap_neo4j_schema
```

Validates: `curl http://localhost:7474` returns Neo4j browser. Schema bootstrap
CLI succeeds. API health endpoint `GET /api/v1/health` reports neo4j connected.

### Action 0.C — Write profile migration script

New file: `src/cli/migrate_profile_to_neo4j.py`

Reads `data/reference_data/profile/base_profile/profile_base_data.json` and creates:
- 1 `Profile` node
- N `Experience` nodes with `HAS_EXPERIENCE` edges
- N `Skill` nodes with `DEMONSTRATES` edges (from experience keywords + skills section)
- N `Education` nodes with `HAS_EDUCATION` edges
- N `Language` nodes with `SPEAKS` edges
- N `Publication` nodes with `PRODUCED` edges
- 1 `LegalStatus` node with `HAS_LEGAL_STATUS` edge

Each node gets a stable UUID (deterministic from content hash, not positional).

Validates: Cypher query `MATCH (p:Profile)-[r]->(n) RETURN type(r), count(n)` shows
all expected relationships. Profile can be round-tripped (export from Neo4j matches
original JSON semantically).

### Action 0.D — Write job artifact migration script

New file: `src/cli/migrate_job_to_neo4j.py`

For a given `--source --job-id`, reads the filesystem artifact chain and creates:
- 1 `JobPosting` node (from scrape approved state + raw metadata)
- 1 `Institution` node + `OrganizationalUnit` chain (from raw source text, LLM-assisted)
- N `Requirement` nodes with `HAS_REQUIREMENT` edges (from extract approved state)
- 1 `PositionTerms` node (parsed from constraints in extract state)
- 1 `ApplicationMethod` node (parsed from constraints + raw text)
- 1 `Person` (contact/PI) node (parsed from raw text)
- N `TextSpan` nodes linking requirements/constraints back to source text offsets
- 1 `Application` node linking `Profile` to `JobPosting`
- N `Match` nodes with `SATISFIES` + `SATISFIED_BY` edges (from match approved state)
- N `ReviewDecision` nodes (from review rounds)
- N `GeneratedDocument` nodes (from generate_documents approved state)

TextSpan derivation: The current `_derive_spans` heuristic in `read_models.py` finds
approximate text offsets by substring matching. The migration script should use the
same approach initially, with a TODO to replace with LLM-annotated spans when the
scraper is updated (Phase 5).

Validates: Run on job 201637. Cypher query shows full subgraph. API view endpoints
can switch from filesystem to Neo4j backend. React views render the same data.

### Action 0.E — Dual-read API layer

Update `src/interfaces/api/read_models.py` to support both filesystem and Neo4j
backends. Configuration flag in `config.py`: `DATA_BACKEND = "filesystem" | "neo4j"`.

This allows incremental migration — filesystem backend stays working while Neo4j
is being validated.

Validates: Both backends produce identical API responses for job 201637.

---

## Next: Phase 1 completion (interactive Doc-to-Graph)

### Action 1.A — Comment data model

Define in Neo4j schema and Python models:
- `(:Comment {id, text, category, created_date, stage, author})`
- `(:Comment)-[:ANNOTATES]->(target node)`
- `(:Comment)-[:CATEGORIZED_AS]->(:FeedbackCategory {name, target_layer})`

API endpoints:
- `POST /api/v1/{source}/{job_id}/comments` — create comment on a node
- `GET /api/v1/{source}/{job_id}/comments` — list comments for a job
- `PATCH /api/v1/{source}/{job_id}/comments/{id}` — edit comment
- `DELETE /api/v1/{source}/{job_id}/comments/{id}` — delete comment

React component: `CommentPanel.tsx` — displays comments on selected node, input
for new comment with category selector.

### Action 1.B — Node property editor

React component: `NodePropertyEditor.tsx` — form rendering based on node label.
Different forms for `Requirement`, `Constraint`, `Institution`, etc.

API endpoint:
- `PATCH /api/v1/nodes/{node_id}` — update node properties

### Action 1.C — Text selection to node creation

React: Add selection handler to source text pane. On selection:
1. Show dialog with node type selector (Requirement, Constraint, Institution, etc.)
2. Pre-fill properties from selected text
3. On submit: `POST /api/v1/{source}/{job_id}/nodes` creates node + TextSpan

API endpoint:
- `POST /api/v1/{source}/{job_id}/nodes` — create node with TextSpan link

---

## Next: Phase 2 completion (interactive Graph Explorer)

### Action 2.A — Review decision UI

React component: `ReviewDecisionPanel.tsx` — three buttons (Approve, Request
Regeneration, Reject) + feedback text area.

API endpoint:
- `POST /api/v1/{source}/{job_id}/stages/{stage}/review` — submit review decision

Backend: Creates `ReviewDecision` node in Neo4j. Updates `Application.status`.
If needed, writes legacy `decision.md` for pipeline compatibility during transition.

### Action 2.B — Node/edge mutation

API endpoints:
- `PATCH /api/v1/nodes/{node_id}` — update node properties
- `DELETE /api/v1/nodes/{node_id}` — delete node and connected edges
- `PATCH /api/v1/edges/{edge_id}` — update edge properties (e.g., match score)
- `DELETE /api/v1/edges/{edge_id}` — delete edge

React: Context menu or selection-based actions on Cytoscape nodes/edges.

---

## Next: Phase 3 completion (interactive Graph-to-Doc)

### Action 3.A — Wire Slate.js into View 3

Replace `<textarea>` with `RichTextPane` component in `ViewThreeGraphToDoc.tsx`.
Add custom Slate decorations for highlighting text spans linked to graph nodes.

### Action 3.B — Bidirectional text-to-node linking

When user selects text in Slate editor, find contributing graph nodes and highlight
them in Cytoscape panel. When user clicks graph node, scroll Slate editor to the
relevant text section and apply highlight decoration.

This requires a `content_map` linking document sections to source graph nodes.
For `generate_documents`, this maps:
- CV summary → `Match` nodes with high scores
- CV injections → `Experience` nodes by `experience_id`
- Letter paragraphs → `Match` + `Requirement` nodes

### Action 3.C — Comment categorization

Extend `CommentPanel` for View 3 with category selector:
- Profile correction (target_layer: "profile")
- Redaction issue (target_layer: "redaction")
- Match calibration (target_layer: "matching")
- Other (target_layer: user-entered)

System suggestion: Basic keyword matching on comment text to suggest category.

---

## Testing Strategy

### Per-action tests

Each action should produce:
1. **Backend**: API endpoint tests (request/response contract, error cases)
2. **Neo4j**: Integration tests using a test Neo4j instance or testcontainers
3. **Frontend**: Component tests for new React components (vitest + testing-library)

### End-to-end validation

After each phase completion:
1. Import all 7 TU Berlin jobs into Neo4j
2. Walk through the full review workflow in the browser
3. Verify all three views render correctly with real data
4. Verify mutations persist and are reflected on page refresh

---

## Dependencies and Environment

### Required packages (not yet installed)

Python:
```
fastapi
uvicorn
neo4j
```

Node (already in `apps/review-workbench/package.json`):
```
react, react-dom, react-router-dom
cytoscape, react-cytoscapejs
slate, slate-react
```

### Docker

```yaml
# docker-compose.neo4j.yml already exists
neo4j:5-community on port 7474 (browser) / 7687 (bolt)
```
