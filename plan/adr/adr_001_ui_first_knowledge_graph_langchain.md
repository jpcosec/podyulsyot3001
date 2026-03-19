# ADR-001: UI-First Review Workbench with Knowledge Graph and Full LangChain Migration

**Date:** 2026-03-16
**Status:** Proposed (Phase 0 scaffold in progress)
**Supersedes:** `plan/subplan/langchain_langgraph_adoption_evaluation.md`
**Implementation tracking:** `plan/adr_001_execution_tracker.md`
**Next actions:** `plan/adr_001_next_actions.md`

## 1. Context

PhD 2.0 is a pipeline producing PhD application artifacts from job postings. The current implementation covers 1 scraping source and 7 jobs, but must scale to **1000+ jobs, ~200 applications, multiple sources**, with full review historization and cross-job querying.

### Current failures driving this decision

1. **Extraction quality**: Flat JSON schemas lose structured information (dates, salary, institution, requirement domains). LLM output drifts between runs (Spanish leakage in `analysis_notes`, uncontrolled `constraint_type`, placeholder defaults in letter fields).
2. **Fragile identity**: Evidence IDs are positional counters generated at runtime by `_profile_base_to_evidence()`. Adding a profile entry shifts all downstream IDs, making match results across pipeline runs incomparable.
3. **No cross-referencing**: Experience-Skills, Publication-Project, Education-equivalency-Requirements are implicit. The LLM must rediscover these relationships from text on every invocation.
4. **No review historization**: No way to track how match quality or reviewer feedback evolve across applications.
5. **No feedback routing**: Reviewer corrections are not categorized or routed back to the appropriate layer (profile vs. run threshold vs. redaction style).
6. **Markdown HITL does not scale**: Editing `decision.md` files works for 7 jobs. It does not work for 200.
7. **Custom AI plumbing debt**: `LLMRuntime` and `PromptManager` duplicate LangChain capabilities without tracing, multi-provider support, or ecosystem alignment.
8. **Critical information lost in extraction**: Analysis of 3 TU Berlin postings (201637, 201601, 201578) showed that PI name, contact email, research topics, institute name, teaching obligation distinction, salary grade, and application logistics are present in every posting but never captured in the extraction schema.

### Design principle: UI-first

The review interface defines the contract between human and machine. The graph schema, pipeline nodes, and persistence layer exist to serve what the views need. We define the interface first, then build the infrastructure to support it.

### Scale target

| Dimension | Current | Target |
|-----------|---------|--------|
| Job postings | 7 | 1,000+ |
| Scraping sources | 1 (TU Berlin) | 10+ (university pages, job boards, LinkedIn) |
| Active applications | 1 | ~200 |
| Profile versions | 1 static JSON | Evolving knowledge graph with review-driven updates |
| Cross-job queries | None | "Which jobs need German B2?", "Where did my ML experience score > 0.8?" |

## 2. Decision

### 2.1 Build a Review Workbench as the primary HITL interface

A React/TypeScript web application that replaces the markdown file review loop.

#### Navigation model

```
Root: Application Portfolio
+-- Profile View
|   +-- Knowledge Graph (skills, experience, education, publications, languages)
|   +-- Base CV template (editable, graph-linked)
|   +-- Base motivation letter template (editable, graph-linked)
|
+-- Job <id> (<source> - <title>)
|   +-- Stage: Scrape       [View 2: Doc-to-Graph]   status indicator
|   +-- Stage: Extract      [View 2: Doc-to-Graph]   status indicator
|   +-- Stage: Translate    [auto/configurable]       status indicator
|   +-- Stage: Match        [View 1: Graph]           status indicator
|   +-- Stage: Generate     [View 3: Graph-to-Doc]    status indicator
|   +-- Stage: Render       [View 3: Graph-to-Doc]    status indicator
|
+-- Job <id> (...)
+-- ...
```

Each stage has a **configurable gating policy**: explicit approval required, or auto-advance if no comments/rejections.

#### Three view modes

**View 1: Graph Explorer** — for match review, feedback history, and relationship inspection.

- Interactive graph visualization: profile, job, matches, documents
- Click any node to inspect/edit properties or delete it
- Click any edge to see score, reasoning, evidence
- Review history timeline across rounds
- Feedback loop visualization: which corrections fed back where
- Select nodes/edges to add free-text comments with manual category tags
- Text selection anywhere creates a new comment or node

**View 2: Document to Graph** — for scraping and extraction review.

- Split pane: source document (left) + extracted graph nodes (right)
- **Bidirectional highlighting**: hover text span, connected nodes highlight; click node, source text spans highlight
- **Select text to create node**: select "Salary grade 13 TV-L", dialog to create a `Constraint` node with typed properties
- **Select existing node**: source text spans highlighted in the document
- Edit/delete any extracted node
- Add comments on extraction quality
- Primary purpose: validate and correct what the LLM extracted from raw text

**View 3: Graph to Document** — for generation and redaction review.

- Split pane: generated document (left) + contributing graph nodes (right)
- Bidirectional linking: select text in document, see which graph nodes (claims, evidence, matches) produced it
- **Direct text editing**: select text to write corrections or redaction comments
- Comments are manually categorized (with system suggestions) into:
  - **Profile corrections**: update profile knowledge graph
  - **Redaction issues**: per-run or threshold-adjustable style parameter
  - **Match calibration**: adjust confidence/exaggeration thresholds
  - **Other**: open-ended, system learns new categories over time
- Each pipeline stage that produces reviewable output gets its own instance of this view

#### Comment and annotation model

Every graph node and edge is **commentable**:
- Free-text annotation, persisted as `(:Comment)` nodes in Neo4j
- Manual category tag (profile, redaction, match_calibration, other) with system-suggested auto-classification
- Comments link to the graph node/edge they annotate and the pipeline stage that produced them
- After review, the system collects comments and routes them to the appropriate feedback channel

#### Tech stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | React + TypeScript | Rich DOM interactions (text selection, highlighting, graph editing) |
| Graph visualization | Diagrammatic-UI | Purpose-built React graph renderer with rich node/edge presentation and reusable layout modes |
| Rich text with annotations | Slate.js | Programmable rich text editor with custom decorations, inline annotations, text selection events |
| Backend API | FastAPI (Python) | Bridges React frontend to Neo4j and pipeline; Python-native for LangChain integration |
| Graph database | Neo4j 5 Community (Docker) | Knowledge graph persistence, Cypher queries, relationship traversal |
| Pipeline orchestration | LangGraph (Python) | Existing graph orchestration, checkpoint/resume, conditional routing |

### 2.2 Adopt Neo4j as the primary data store

Replace flat JSON artifact files with a Neo4j knowledge graph.

#### Schema

The schema is organized into five domains. Every node that originates from a source document carries a `TextSpan` relationship for View 2 bidirectional highlighting.

**Profile domain** — the candidate's evolving knowledge graph.

```cypher
(:Profile {id, version, snapshot_date})
  -[:HAS_EXPERIENCE]-> (:Experience {id, role, organization, location, start_date, end_date, tenure_months, keywords[]})
    -[:DEMONSTRATES]-> (:Skill {id, name, domain, proficiency_level})
    -[:PRODUCED]-> (:Publication {id, title, venue, year, url})
    -[:PARTICIPATED_IN]-> (:Project {id, name, role, stack[]})
  -[:HAS_EDUCATION]-> (:Education {id, degree, field, institution, graduation_year, equivalency_status, equivalency_authority})
  -[:SPEAKS]-> (:Language {id, name, cefr_level, notes})
  -[:HAS_SKILL]-> (:Skill {id, name, domain, proficiency_level})
  -[:HAS_LEGAL_STATUS]-> (:LegalStatus {visa_type, work_permission_de, valid_until})
```

**Job domain** — everything extracted from a posting. Structured to match the actual information present in university job board postings (derived from Stellenticket template analysis of 3 TU Berlin postings).

```cypher
// Core posting identity
(:JobPosting {id, source, source_url, scraped_date, published_date, original_language, title, reference_number})

// Organizational hierarchy — who posted it, where
(:JobPosting)-[:POSTED_BY]->(:Institution {id, name, type})
(:Institution)-[:HAS_UNIT]->(:OrganizationalUnit {id, name, level})
  // level: "faculty" | "institute" | "research_group"
  // e.g. Faculty IV -> Institute for Software Engineering -> DIMA
(:OrganizationalUnit)-[:LED_BY]->(:Person {id, name, title, role, email})

// What the position is about — research context
(:JobPosting)-[:HAS_RESEARCH_CONTEXT]->(:ResearchContext {id, description})
(:ResearchContext)-[:COVERS_TOPIC]->(:ResearchTopic {id, name, field})
(:ResearchContext)-[:INVOLVES_PROJECT]->(:ResearchProject {id, name, description, funding_source})

// What the position requires — the candidate profile demands
(:JobPosting)-[:HAS_REQUIREMENT]->(:Requirement {id, text, priority, domain, is_blocker})
  // priority: "must" | "should" | "nice"
  // domain: "education" | "language" | "technical" | "research" | "teaching" | "soft_skill" | "administrative"
  // is_blocker: true if failing this requirement should prevent application

// Position terms — structured, not a flat bag
(:JobPosting)-[:HAS_TERMS]->(:PositionTerms {
    employment_type,       // "full_time" | "part_time" | "either"
    duration,              // "5 years" | "20 months"
    duration_months,       // 60 | 20 (parsed integer)
    start_date,            // ISO date or "earliest_possible"
    salary_grade,          // "E13" | "E14"
    salary_scale,          // "TV-L Berliner Hochschulen"
    has_teaching_obligation,  // true | false
    part_time_possible,    // true | false
    funding_caveat         // "subject to funding approval" | null
})

// Teaching duties (when has_teaching_obligation is true)
(:JobPosting)-[:HAS_TEACHING_DUTY]->(:TeachingDuty {id, description, course_name, language})

// Application logistics — how to actually apply
(:JobPosting)-[:HAS_APPLICATION_METHOD]->(:ApplicationMethod {
    deadline,              // ISO date
    email,                 // application submission email
    postal_address,        // full postal address if accepted
    reference_number,      // must quote in subject
    format,                // "single PDF" | "multiple documents"
    max_size,              // "3 MB" | "5 MB"
    required_documents[],  // ["cover_letter", "cv", "certificates", "grades", "publications", "references"]
    notes                  // "submit copies only", "no return of documents"
})

// Contact person (often the PI, needed for letter/email salutation)
(:JobPosting)-[:HAS_CONTACT]->(:Person {id, name, title, role, email})

// Metadata and classification
(:JobPosting)-[:TAGGED_AS]->(:DomainTag {name})
  // e.g. "Academia and research", "Teaching (university)", "IT"
(:JobPosting)-[:HAS_LEGAL_NOTICE]->(:LegalNotice {type, text, url})
  // type: "equal_opportunity" | "gdpr" | "accessibility"
```

**Application domain** — per job-profile pair, tracking the full pipeline.

```cypher
(:Application {id, job_id, profile_version, status, created_date})
  -[:TARGETS]-> (:JobPosting)
  -[:USES_PROFILE]-> (:Profile)
  -[:HAS_MATCH]-> (:Match {req_id, score, reasoning, round})
    -[:SATISFIES]-> (:Requirement)
    -[:SATISFIED_BY]-> (:Experience | :Education | :Skill | :Publication | :Language)
  -[:HAS_REVIEW]-> (:ReviewDecision {stage, round, decision, timestamp, feedback_summary})
  -[:HAS_DOCUMENT]-> (:GeneratedDocument {type, version, deltas_hash, content_ref})
```

**Annotation domain** — comments and feedback on any node.

```cypher
(:Comment {id, text, category, created_date, stage, author})
  -[:ANNOTATES]-> (any node)
  -[:CATEGORIZED_AS]-> (:FeedbackCategory {name, target_layer})
  // target_layer: "profile" | "extraction" | "matching" | "generation" | "redaction" | "threshold"
  // category is user-assigned (free text initially, system suggests from known categories)
```

**Source provenance domain** — linking extracted nodes back to source text.

```cypher
(:TextSpan {id, start_offset, end_offset, text_preview, source_document_ref})
  -[:EXTRACTED_TO]-> (any node in Job domain)
  -[:IN_DOCUMENT]-> (:SourceDocument {id, job_id, content_hash, format})
```

Every node in the Job domain that was extracted from text should have at least one incoming `EXTRACTED_TO` edge from a `TextSpan`. This enables View 2 bidirectional highlighting. When the user selects text in the source document, the system finds overlapping `TextSpan` nodes and follows edges to the extracted graph nodes. When the user clicks a graph node, the system follows edges back to `TextSpan` nodes and highlights the corresponding ranges in the source document.

#### Key relationships solving current problems

| Current problem | Graph solution |
|----------------|----------------|
| Evidence IDs are positional | Stable UUID node IDs in Neo4j |
| Experience-Skill implicit | `(:Experience)-[:DEMONSTRATES]->(:Skill)` explicit edges |
| Education equivalency lost | `(:Education {equivalency_status, equivalency_authority})` as properties |
| No cross-job queries | Cypher: `MATCH (r:Requirement) WHERE r.domain = "language" RETURN r` |
| No review history | `(:ReviewDecision)` nodes per stage per round, linked to application |
| Feedback not routed | `(:Comment)-[:CATEGORIZED_AS]->(:FeedbackCategory {target_layer})` |
| Extraction provenance lost | `(:TextSpan)-[:EXTRACTED_TO]->(:Requirement)` preserves source location |
| PI name / contact lost | `(:JobPosting)-[:HAS_CONTACT]->(:Person {name, title, email})` |
| Research topics lost | `(:ResearchContext)-[:COVERS_TOPIC]->(:ResearchTopic)` |
| Institute hierarchy lost | `(:Institution)-[:HAS_UNIT]->(:OrganizationalUnit)` chain |
| Constraint type drift | `(:PositionTerms)` with typed properties instead of free-text bag |
| Teaching vs non-teaching | `(:PositionTerms {has_teaching_obligation})` + `(:TeachingDuty)` nodes |
| Application logistics lost | `(:ApplicationMethod)` with structured deadline, email, format, documents |
| Salary not comparable | `(:PositionTerms {salary_grade: "E13", salary_scale: "TV-L"})` parsed |
| Duration not comparable | `(:PositionTerms {duration_months: 60})` parsed integer |

### 2.3 Full LangChain migration

| Component | Current | Target |
|-----------|---------|--------|
| Model invocation | `LLMRuntime` (custom Gemini wrapper) | `ChatGoogleGenerativeAI` from `langchain-google-genai` |
| Structured output | Custom Pydantic validation | `.with_structured_output(Schema)` |
| Prompt rendering | `PromptManager` (custom Jinja2) | `ChatPromptTemplate` wrapping existing Jinja2 templates |
| Tracing | None | LangSmith |
| Multi-provider | Gemini only | Configurable: Gemini, OpenAI, Anthropic |
| Error handling | Custom exceptions | LangChain exceptions mapped to `ErrorContext` |
| Orchestration | LangGraph `StateGraph` | LangGraph `StateGraph` (deepened) |

Prompt file discipline: Node-local `system.md` and `user_template.md` files remain. They are loaded by a thin adapter that wraps them in `ChatPromptTemplate`. The strict XML-tag validation from `PromptManager` is preserved as a custom validator in the chain.

### 2.4 Hybrid scraping architecture

| Source type | Strategy |
|-------------|----------|
| Known structured sites (TU Berlin, university HR portals) | Dedicated adapter + deterministic field extraction |
| Semi-structured sites (Indeed, LinkedIn) | Adapter + LLM normalization |
| Unknown/long-tail sites | LLM extraction: raw HTML to graph nodes via structured output |

All scrapers produce the same output: Neo4j nodes (`JobPosting`, `Requirement`, `Constraint`, `Institution`, `ResearchTopic`) with `TextSpan` provenance linking back to source text positions.

## 3. Implementation Sequence

**UI-first**: build the review interface before deepening the pipeline. The pipeline adapts to serve what the interface needs.

### Phase 0: Foundation (Neo4j + FastAPI + React scaffold)

- Neo4j Docker setup with schema constraints
- FastAPI backend with Neo4j driver, basic CRUD endpoints for graph nodes
- React app scaffold with routing, Diagrammatic-UI graph integration, Slate.js integration
- Import existing profile data into Neo4j (migrate `profile_base_data.json`)
- Import one job's artifact chain into Neo4j (migrate 201637 data)

### Phase 1: View 2 — Document to Graph (Scraping/Extraction Review)

- Implement split-pane: source document + graph panel
- Bidirectional highlighting with `TextSpan` nodes
- Text selection to node creation dialog
- Node property editor
- Comment system on nodes
- Wire to existing scrape/extract pipeline output

### Phase 2: View 1 — Graph Explorer (Match Review)

- Interactive graph visualization with Diagrammatic-UI
- Match edge inspection (score, reasoning, evidence)
- Node/edge editing and deletion
- Review decision interface (approve/request_regen/reject)
- Comment system on edges

### Phase 3: View 3 — Graph to Document (Generation Review)

- Split-pane: generated document + contributing graph nodes
- Bidirectional linking between text sections and source nodes
- Direct text editing with Slate.js
- Comment categorization (profile/redaction/match_calibration/other)
- Feedback routing pipeline

### Phase 4: Portfolio Dashboard + Navigation

- Job tree with stage status indicators
- Profile view with editable knowledge graph
- Base document template views
- Cross-job filtering and querying
- Configurable stage gating policies

### Phase 5: LangChain Migration + Pipeline Adaptation

- Replace `LLMRuntime` with `ChatGoogleGenerativeAI`
- Replace `PromptManager` with `ChatPromptTemplate` wrappers
- Add LangSmith tracing
- Pipeline nodes write to Neo4j instead of JSON files
- Scraper nodes produce `TextSpan` provenance

### Phase 6: Multi-Source Scraping + Scale

- Per-source adapter framework
- LLM fallback scraper for unknown sites
- Batch scraping CLI
- Scale testing with 1000+ jobs

## 4. Consequences

### What changes

1. **HITL interface**: Markdown files to React review workbench with three view modes
2. **Data plane**: JSON files on disk to Neo4j knowledge graph
3. **AI layer**: Custom `LLMRuntime`/`PromptManager` to Full LangChain
4. **Identity**: Positional counters to Stable Neo4j UUIDs
5. **Feedback loop**: Unstructured to Categorized comments routed to profile/threshold/style layers

### What stays

1. **LangGraph orchestration** with conditional edges, interrupt_before, SQLite checkpointing
2. **Fail-closed semantics** at every review gate
3. **Delta-based document generation** (DocumentDeltas + Jinja templates)
4. **Control plane minimalism** (GraphState carries routing signals + Neo4j references)
5. **Batch/on-demand operational model**

### Risks

| Risk | Mitigation |
|------|------------|
| React frontend is a significant new codebase | Start with MVP views; use component libraries (shadcn/ui, etc.) |
| Neo4j adds operational complexity | Single Docker container; `neo4j-admin dump` for backups; schema constraints |
| Full LangChain migration may regress fail-closed behavior | Migrate one node at a time; preserve test suite; add error mapping tests |
| Bidirectional text-to-graph linking is technically complex | Implement TextSpan model carefully; start with read-only highlighting before editing |
| UI development delays pipeline improvements | Phase 5 (pipeline) is independent; can parallelize after Phase 0 |

### Non-negotiable constraints preserved

1. Fail-closed behavior at every review gate
2. Deterministic routing: approve / request_regeneration / reject
3. No data payloads in GraphState (only Neo4j references)
4. Downstream nodes consume only approved upstream data
5. Human approval required at configured gates

## 5. Alternatives Considered

1. **Lightweight graph (networkx + JSON-LD)**: Lower ops burden but does not support the target scale of 1000+ jobs with cross-job queries. Would require migration to Neo4j later.
2. **Hybrid LangChain adoption** (original recommendation from `plan/subplan/langchain_langgraph_adoption_evaluation.md`): Lower risk but perpetuates custom maintenance burden and misses tracing/multi-provider benefits.
3. **Streamlit for review UI**: Insufficient for the required interaction patterns (text selection, bidirectional highlighting, inline editing, graph manipulation). These are fundamentally DOM-level interactions that need a real frontend framework.
4. **Keep current architecture, fix incrementally**: The flat JSON schema and positional IDs are fundamentally limiting. Incremental fixes would fight the architecture rather than fix it. Proposing lightweight tools because the project is small is circular reasoning when the goal is to grow it 100x.

## 6. Deployment

| Component | Deployment |
|-----------|-----------|
| Neo4j | Docker: `neo4j:5-community`, local, persistent volume |
| FastAPI | Local Python process, `uvicorn` |
| React app | Local dev server (`vite`), or built static files served by FastAPI |
| LangGraph pipeline | Local Python process, SQLite checkpoints |
| LangSmith | Cloud (free tier) for tracing |
