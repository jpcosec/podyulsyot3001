# UI Plan In-Depth Review — Design Spec

## Purpose

Single document that serves as both **build manual** (architecture, objectives, guardrails, libraries, testing) and **review checklist** (verification criteria for humans and agents). Replaces the existing 18 plan docs in `plan/ui/ui_plan/`.

## Decisions from brainstorming

- **CvGraphEditor is eliminated.** Its capabilities are requirements for the NodeEditor. Step 00b maps every feature to its new home.
- **elkjs from the start.** No dagre. Compound/nested layout natively.
- **Library-first, no speculative abstraction.** Use React Flow, elkjs, zustand, FlexLayout, RJSF directly. No wrapper modules for hypothetical portability.
- **Representation Schema** — per-project YAML/JSON config that maps neo4j graph structure to editor behavior (node types, containment, relations, visual mappings, views). The editor is domain-agnostic by configuration.
- **CSS Theme** — Obsidian-style overridable CSS. Schema sets `data-*` attributes, CSS targets them. MD3 token system as default theme (Manrope + Inter, glass panels, dot grid).
- **Color scales** — schema declares scales as defaults, CSS overrides win.
- **Extension Model** — one `registry.register()` pattern for every extension type. Built-in features use the same API. 10 extension types.
- **Panel docking** — user-configurable via FlexLayout-react. Left/right/float, saved per view preset.
- **Schema-driven inspector** — RJSF renders forms from representation schema attributes compiled to JSON Schema.
- **Performance** — render tiers (only focused node gets expensive renderer), prerender cache, background precomputation, compiled registry lookup tables (O(1) at render time).
- **Testing** — ideal approach: Vitest (unit), @testing-library/react (component), Playwright (integration). Bootstrap from scratch.
- **Gap analysis** — inline per step + consolidated gap matrix.
- **Library decisions** — decision matrix per choice point with recommendation + switch trigger.

---

## File Structure

```
plan/ui/ui_plan/
├── README.md                           # master index + dependency graph + build order
├── 00_status_matrix.md                 # live capability status tracker
├── 00_gap_matrix.md                    # consolidated gaps across all steps
├── 00_library_decisions.md             # all library decision matrices
├── 00_test_infrastructure.md           # Vitest + Testing Library + Playwright bootstrap
│
├── 00b_cvgraph_capability_map.md       # CvGraphEditor → new architecture mapping
├── 00c_representation_schema.md        # schema format, validation, loading, views
├── 00d_css_theme_system.md             # MD3 tokens, Obsidian-style overrides, color scales
├── 00e_extension_model.md              # extension registry, 10 extension types, activation rules
│
├── 01_graph_foundations.md             # state contract, persistence boundary
├── 01a_layout_and_view_presets.md      # elkjs, named presets, view defaults
├── 01b_node_type_registry_and_modes.md # schema-driven registry, renderers, dispatcher
├── 01c_editor_state_and_history.md     # action taxonomy, undo/redo, dirty detection
│
├── 02_structured_docs_and_subflows.md  # containers, nesting, proxy edges, drag interactions
├── 02a_tree_mode_and_outline_sync.md   # sidebar tree, bidirectional sync
│
├── 03_rich_content_nodes.md            # shared payload contract, anchor model
├── 03a_text_annotation_links.md        # anchor selectors, confidence tracking
├── 03b_markdown_formatted_editor.md    # source/preview split
├── 03c_json_yaml_views.md             # tree inspector, validated edit, key-path anchors
├── 03d_table_editor.md                # TanStack Table, typed columns
├── 03e_code_display_and_annotation.md  # CodeMirror 6, line-range anchors
├── 03f_image_annotation.md            # rectangle regions, normalized coords
│
├── 04_external_data_and_schema.md      # source adapters, ingestion pipeline
├── 04a_document_explorer.md            # schema/view switching, asset browsing
│
├── 05_validation_and_test_impact.md    # impact registry, verification matrix
│
└── AGENT_REVIEWER_ENTRYPOINT.md        # review protocol for agents
```

## 7-Section Template

Every step file follows this structure:

```
# {Step Name}

## 1. Architecture Logic
   Components, responsibilities, data flow, integration points.

## 2. Objectives
   Numbered, testable acceptance criteria.

## 3. Don'ts
   Anti-patterns and traps specific to this step.

## 4. Known Gaps & Open Questions
   Unresolved items with severity. Cross-references to 00_gap_matrix.md.

## 5. Library Decision Matrix
   Candidates with: bundle size, API style, integration cost,
   maintenance risk, recommendation, switch trigger.
   Cross-references to 00_library_decisions.md.

## 6. Test Plan
   Unit, component, integration tests.
   What to assert, what fixtures are needed.

## 7. Review Checklist
   Binary yes/no checks for humans and agents.
```

---

## Technology Stack

| Concern | Library | Status |
|---|---|---|
| Graph canvas | @xyflow/react (React Flow) | In use |
| Layout engine | elkjs | Committed, replaces dagre |
| State management | zustand | Committed |
| Dockable panels | flexlayout-react | Committed |
| Schema-driven forms | @rjsf/core + @rjsf/utils + custom theme | Committed |
| Extension registry | Custom (~300 lines) | To build |
| Explorer tree | react-arborist | Committed |
| Icons | Material Symbols Outlined | In mockups |
| CSS framework | Tailwind CSS + MD3 tokens as CSS vars | In use |
| Typography | Manrope (headlines) + Inter (body) | In mockups |
| Graph database | neo4j + neo4j-driver | Committed |
| Unit testing | Vitest | Committed |
| Component testing | @testing-library/react | Committed |
| Integration testing | Playwright | In use (partially) |
| Markdown editor | TBD (decision matrix in 03b) | Deferred |
| Code editor | CodeMirror 6 (recommended, matrix in 03e) | Deferred |
| JSON/YAML inspector | TBD (decision matrix in 03c) | Deferred |
| Table editor | TanStack Table (recommended, matrix in 03d) | Deferred |
| Image annotation | TBD (decision matrix in 03f) | Deferred |

---

## Build Order

```
FOUNDATION
  00b  CvGraphEditor Capability Map
  00c  Representation Schema Spec
  00d  CSS Theme System
  00e  Extension Model
  00   Test Infrastructure Bootstrap

GRAPH ENGINE
  01   Graph Foundations (state contract, persistence)
  01a  Layout & View Presets (elkjs, named presets)
  01b  Node Type Registry & Modes (schema-driven)
  01c  Editor State & History (actions, undo/redo)

STRUCTURE
  02   Structured Documents & Subflows (containers, nesting)
  02a  Tree Mode & Outline Sync (sidebar tree)

CONTENT
  03   Rich Content Nodes (shared contract)
  03a  Text Annotation Links (anchor model)
  03b  Markdown Formatted Editor
  03c  JSON/YAML Views
  03d  Table Editor
  03e  Code Display & Annotation
  03f  Image Annotation

DATA
  04   External Data & Schema Integration (adapters)
  04a  Document Explorer (navigation)

OPERATIONS
  05   Validation & Test Impact Map
```

---

## Step 00b — CvGraphEditor Capability Map

### 1. Architecture Logic

Before building: map every CvGraphEditor feature to where it lives in the new architecture. This is the migration contract — nothing gets lost, nothing gets ported blindly.

| CvGraphEditor Feature | Step | How It Maps |
|---|---|---|
| Group nodes (per-category containers) | 01b | Container node type with container_config. Categories are metadata, not hardcoded groups. |
| Entry nodes (category, essential, descriptions) | 01b | Structured entry node type in registry. Payload carries category, essential flag, description array. |
| Skill ball nodes (mastery, shape, color) | 01b | Skill node type in registry. Mastery scale in payload. Visual style derived from mastery + category via schema. |
| Expand/collapse containers | 02 | Container collapse/expand with summary + child count. Generic, not CV-specific. |
| Proxy edges when collapsed | 02 | Proxy edge rendering as container behavior. Dashed style, deduplication. |
| Drag reorder within group | 02 | Container child reorder via order array. Semantic action, undoable. |
| Drag across groups | 02 | Cross-container move. Semantic action, undoable. |
| Drag connect entry→skill | 01 | Standard edge creation. "demonstrates" is a relation type. |
| Entry expand panel (right slide-in) | 01b | edit_in_context renderer mode for entry node type. |
| Skill palette sidebar | 02a / 00e | Sidebar panel extension showing available nodes of a type. |
| Mastery scale (5-level) | 01b | Payload metadata. Rendering via schema visual config + CSS theme. |
| API persistence (GET/PUT) | 01 | Pluggable persistence API. CV profile graph is one adapter. |
| Dagre layout | 01a | Replaced by elkjs. |
| Dynamic container height | 01a | elkjs compound layout computes bounds from children. |
| Dirty detection + save/discard | 01c | Action-count dirty detection. Save/discard in toolbar. |

### 2. Objectives

1. Every CvGraphEditor feature has a named home in the new architecture
2. No feature is lost — this table is the verification checklist
3. When the NodeEditor can reproduce all rows, CvGraphEditor is deleted

### 3. Don'ts

- **Don't port CvGraphEditor code directly.** Features are requirements, not implementations.
- **Don't keep CvGraphEditor alive after migration.** Once all rows pass, delete it.
- **Don't add CV-specific logic to the generic editor.** Entry, skill, mastery are node types and payload shapes. The editor is type-agnostic.

### 4. Known Gaps & Open Questions

None — this step is purely a mapping document.

### 5. Library Decision Matrix

N/A — no libraries needed for this step.

### 6. Test Plan

N/A — this step produces a document, not code.

### 7. Review Checklist

- [ ] Every CvGraphEditor feature is listed with a target step
- [ ] No feature is marked "not needed" without explicit justification
- [ ] The mapping table is referenced by all downstream steps

---

## Step 00c — Representation Schema Spec

### 1. Architecture Logic

The representation schema is a per-project YAML/JSON configuration that makes the editor domain-agnostic. It sits between the neo4j canonical base (all data, all attributes) and the editor (which only shows what the schema declares).

**Schema shape:**

```yaml
schema_id: string
display_name: string
theme: ./path/to/theme.css
max_nesting_depth: 3           # default 3, configurable per project

sources:
  - type: neo4j | json_file | api | yaml_file
    # source-specific config

node_types:
  <type_id>:
    label: string              # neo4j label
    display_name: string
    content_type: string       # maps to renderer (entity, container, markdown_text, etc.)
    is_container: boolean
    allowed_children: [type_id]
    container_config:              # only if is_container: true
      child_ordering: manual | attribute  # how children are ordered
      ordering_attribute: string   # if attribute-ordered
      collapse_behavior: summary | hide  # what shows when collapsed
      proxy_edge_style: dashed | dotted  # style for proxy edges
    visual:
      icon: string             # Material Symbol name
      shape: string            # circle, card, diamond, etc.
      color_from: attribute    # attribute → data-* → CSS
      color_scale:             # computed scale, CSS overrides win
        attribute: string
        palette: string
        min: number
        max: number
      size_from: attribute
      badge_from: attribute
    attributes: [string]       # subset shown in editor (graph can have more)
    render_hints:
      precompute_focus: boolean
      lazy_payload: boolean

relation_types:
  <type_id>:
    source: [node_type_id]
    target: [node_type_id]
    visual:
      style: solid | dashed | none
      color: string
      label_from: attribute
    attributes: [string]

views:
  <view_id>:
    display_name: string
    type: filter | subgraph
    # filter type:
    show_node_types: [type_id] | all
    show_relations: [type_id] | all
    # subgraph type:
    query: string              # Cypher query
    layout: preset_type
    load_attributes: [string] | all
```

**Key principles:**
- The schema is a projection — declares which attributes matter for rendering. The graph can have many more.
- Some attributes are lazy-loaded (e.g., `content_path` resolves a file at runtime).
- Multiple views within one schema: some are filters (same graph, different visibility), some are subgraphs (different Cypher query).
- Schema compiles to JSON Schema at load time for RJSF inspector forms.

**Color scale system:**
- Schema declares `color_scale` with attribute, palette name, min/max.
- Editor computes CSS variables at load time from the scale.
- CSS theme can override any specific value — CSS always wins.

### 2. Objectives

1. Schema format is defined and documented with examples
2. Schema validates at load time (missing required fields, invalid references)
3. At least two example schemas exist: CV Profile, Scraping Knowledge Graph
4. Schema compiles node_type attributes to JSON Schema for RJSF
5. Color scales compute CSS variables, CSS overrides work
6. Views of type `subgraph` declare valid Cypher queries
7. Views of type `filter` declare valid node/relation type references

### 3. Don'ts

- **Don't execute user-composed Cypher.** View queries are declared in the schema. The schema is the security boundary.
- **Don't require all attributes to be declared.** The schema is a projection. Undeclared attributes exist in neo4j but are invisible to the editor.
- **Don't couple the schema format to a specific graph database.** neo4j is the current backend, but the schema describes structure, not Cypher. Source adapters handle the database specifics.
- **Don't validate Cypher at schema parse time.** Syntax-check only. Semantic validation (do these labels exist?) happens at first query execution.

### 4. Known Gaps & Open Questions

- **GAP-SCHEMA-01** (Medium): How to handle schema evolution — what happens when a schema changes but saved data follows the old shape? Suggested: schema_version field + migration functions.
- **GAP-SCHEMA-02** (Medium): Cross-schema views (e.g., notes → skills → CV entries) — the `cross_domain` view example references node types from multiple schemas. Need to define whether this requires a merged schema or explicit cross-references.
- **GAP-SCHEMA-03** (Low): Schema inheritance — can a schema extend another? Deferred until a real use case demands it.

### 5. Library Decision Matrix

- **YAML parsing**: `js-yaml` (lightweight, well-maintained) or `yaml` package (spec-complete, heavier). Recommendation: `js-yaml` — sufficient for config files.
- **JSON Schema compilation**: Built into RJSF pipeline. Representation schema attributes → JSON Schema objects via a compile step we write.
- **Schema validation**: `ajv` (already a dependency via RJSF) for validating schema files against a meta-schema.

### 6. Test Plan

- **Unit**: Schema parses without error for both example schemas. Invalid schemas produce clear errors. Attribute → JSON Schema compilation produces correct field types. Color scale computation produces correct CSS variable values.
- **Component**: Editor loads a schema and populates the registry correctly.
- **Integration**: Load CV Profile schema → switch to Evidence view → correct subgraph renders.

### 7. Review Checklist

- [ ] Schema format documented with full reference
- [ ] Two example schemas exist and parse correctly
- [ ] Schema validates at load time with clear error messages
- [ ] Attributes compile to JSON Schema for RJSF
- [ ] Color scales compute and CSS overrides work
- [ ] View queries are schema-declared, not user-composed

---

## Step 00d — CSS Theme System

### 1. Architecture Logic

The CSS theme is an editable file per project, Obsidian-style. The editor never hardcodes colors, shapes, or sizes — it renders structure, the theme paints it.

**Bridge between schema and CSS:** The schema's `color_from`, `size_from`, `badge_from`, `shape` declarations cause the editor to set `data-*` attributes on DOM elements. The CSS theme targets those attributes.

**Theme layers (cascading):**
1. Editor default variables (built-in fallbacks)
2. Schema-computed scales (from `color_scale` declarations)
3. Project theme file (referenced in schema's `theme` field)
4. CSS always wins — any variable can be overridden

**Default theme:** MD3 token system from the mockups — surface hierarchy, primary/secondary/tertiary containers, glass panels with backdrop-blur, Manrope headlines + Inter body, Material Symbols Outlined icons, dot grid canvas, rounded cards.

### 2. Objectives

1. All visual properties are driven by CSS variables, never hardcoded in components
2. `data-*` attributes are set on DOM elements from schema visual config
3. Default MD3 theme renders all node types correctly
4. A custom .css file can override any visual property
5. Schema color scales generate CSS variables at load time
6. Theme file is hot-reloadable during development

### 3. Don'ts

- **Don't inline styles in React components.** All visual properties via CSS variables or Tailwind utilities that reference CSS variables.
- **Don't hardcode MD3 tokens as the only option.** MD3 is the default theme. The system must work with any CSS file that defines the required variables.
- **Don't couple component structure to theme assumptions.** Components render semantic `data-*` attributes. How those look is the theme's job.

### 4. Known Gaps & Open Questions

- **GAP-THEME-01** (Medium): Dark mode. The mockups show light mode only. Need to decide: is dark mode a second theme file, or does the same theme support both via `prefers-color-scheme`? Suggested: theme files can use media queries, editor doesn't enforce either.
- **GAP-THEME-02** (Low): Theme validation — how to warn when a theme is missing required variables? Suggested: editor logs warnings in dev mode for undefined CSS variables.

### 5. Library Decision Matrix

No additional libraries. Tailwind CSS (already in use) + CSS custom properties + `data-*` attribute selectors.

### 6. Test Plan

- **Unit**: CSS variable computation from schema color scales produces expected values.
- **Component**: Default theme renders all built-in node types without unstyled elements.
- **Integration**: Load custom theme → visual overrides apply → switch back to default → overrides removed.

### 7. Review Checklist

- [ ] No hardcoded colors/sizes in React components
- [ ] `data-*` attributes present on all schema-driven elements
- [ ] Default MD3 theme renders everything
- [ ] Custom theme file overrides apply correctly
- [ ] Color scales generate correct CSS variables

---

## Step 00e — Extension Model

### 1. Architecture Logic

The editor is a host runtime that discovers and mounts extensions at load time. Every feature that varies by domain is an extension. Built-in features use the same API as project extensions. No privileged internal paths.

**One pattern:** Every extension follows: declare → register → mount → communicate via dispatch.

**10 extension types:**

| Type | What it does | Built-in examples |
|---|---|---|
| `node_renderer` | Renders a node type in one or more display modes | entity, container, markdown_text, code_block |
| `sidebar_panel` | Dockable panel (left/right/float via FlexLayout) | Explorer, Outline, Filters, Node Palette |
| `inspector_section` | Tab inside the node inspector | Metadata, Relationships, History |
| `toolbar_action` | Button on the floating bottom toolbar | Zoom, Pan, Relayout, Filter |
| `context_action` | Right-click menu item on node/edge | Layout Focus, Expand Context, Delete |
| `canvas_overlay` | Floating overlay on canvas | Focus Mode status bar, zoom controls |
| `layout_algorithm` | New layout preset type | dag_default, focus_centered, tree_top_down |
| `source_adapter` | New data source type | neo4j, json_file, api |
| `edge_renderer` | Custom edge rendering | solid, dashed, proxy |
| `keyboard_shortcut` | Keyboard binding | Ctrl+Z undo, Delete remove |

**Activation rules:** Extensions declare when they're active. Inactive extensions don't mount.

```
activateWhen:
  schema: "cv_profile"       # only in this schema
  nodeType: "entry"           # only when this type focused
  editorState: "focus"        # EditorState value (browse/focus/focus_relation/edit_node/edit_relation)
  rendererMode: "edit_in_context"  # renderer mode (minimized/focus/edit_in_context/full_editor)
  all: [rule, rule]           # AND
  any: [rule, rule]           # OR
```

Extensions can activate on either EditorState (the 5-state machine from graph_view) or rendererMode (the 4-mode renderer axis from 01b), or both. See 01b for the mapping between these two axes.

**Performance model:**
- **Schema load**: registry compiles all extensions into O(1) lookup tables. Happens once.
- **Mode/view change**: table lookup. Happens rarely.
- **Node focus change**: table lookup + prop update on cached component.
- **Pan/zoom/drag**: zero registry involvement.
- **Prerender cache**: extensions declare cacheable modes. Cached until payload changes.
- **Background precomputation**: idle-time prerender of neighbors' focus mode.

**Panel docking:** FlexLayout-react handles all docking. Panels are sidebar_panel extensions. User drags to reposition. Layout serialized as part of view presets.

**Schema-driven inspector:** RJSF renders forms from representation schema's attributes compiled to JSON Schema. Custom renderers (relation pills, mastery scale, tags) are registered as RJSF custom widgets AND as inspector_section extensions.

**HTML snippets:** `html_safe` content type renders sanitized HTML via DOMPurify (see html_safe section after 03f for sanitization rules).

### 2. Objectives

1. All built-in features are registered through `registry.register()` — same API as project extensions
2. Adding a new extension type requires: one interface definition + one mount slot in the host
3. Activation rules evaluated at compile time (schema load), not per-frame
4. FlexLayout integration: panels dock left/right/float, layout serialized
5. RJSF integration: inspector forms render from schema attributes
6. Prerender cache works for declared cacheable modes
7. Extension developer guide exists with "I want to... → Create this → Register it" table

### 3. Don'ts

- **Don't create privileged internal paths.** Built-in extensions register the same way as external ones.
- **Don't evaluate activation rules on every state change.** Compile lookup tables at schema load. Re-evaluate only on discrete transitions (schema change, mode change, view change).
- **Don't mount invisible extensions.** Inactive or hidden panels don't render React components. Mount on first show, keep mounted (hidden) for reuse.
- **Don't allow extensions to mutate state directly.** All mutations through `dispatch(action)`. Extensions read via selectors.

### 4. Known Gaps & Open Questions

- **GAP-EXT-01** (Medium): Extension packaging — how are third-party extensions distributed? NPM packages? Local files? Deferred until the first external consumer exists.
- **GAP-EXT-02** (Low): Extension conflict resolution — what if two extensions register for the same slot with equal priority? Suggested: last-registered wins, with console warning.

### 5. Library Decision Matrix

- **Dockable panels**: FlexLayout-react — committed. See LIB-DOCK-01.
- **Schema-driven forms**: RJSF — committed. See LIB-FORMS-01.
- **Extension registry**: Custom (~300 lines).

### 6. Test Plan

- **Unit**: registry.register() stores extension. registry.compile() builds correct lookup tables. Activation rules evaluate correctly for all operators (schema, nodeType, mode, all, any).
- **Component**: sidebar_panel extension mounts in FlexLayout. inspector_section extension renders as RJSF custom widget. context_action appears in right-click menu for matching node type.
- **Integration**: Register custom node_renderer → create node of that type → correct renderer mounts in all modes.

### 7. Review Checklist

- [ ] All built-in features registered via registry.register()
- [ ] Lookup tables are O(1)
- [ ] Activation rules compile at schema load
- [ ] FlexLayout panels dock/float/serialize
- [ ] RJSF forms render from schema attributes
- [ ] Prerender cache works for declared modes
- [ ] Developer guide table exists

---

## Step 01 — Graph Foundations

### 1. Architecture Logic

The NodeEditor is the single graph editing surface. It must support everything CvGraphEditor does today while remaining domain-agnostic via the representation schema.

**Four state layers (zustand store):**

- **graph_content** — nodes (with typed payloads), edges (with typed payloads), container relationships (parent_id, child ordering). Domain truth.
- **graph_view** — viewport, selected/focused IDs, collapsed containers, visible relation types, active layout preset, active view, active EditorState (5-state machine: browse/focus/focus_relation/edit_node/edit_relation). Per-session, not persisted by default. `active_view` references a view from the loaded schema (00c). Switching schemas resets `active_view` to the new schema's default view. Switching views within a schema triggers the view's declared query (if subgraph type) or filter application.
- **graph_history** — semantic action log. Only domain mutations, not view changes.
- **external_refs** — pointers to documents, datasources, schemas, annotation anchors. References, not copies. Shape: `{ ref_id, ref_type: "document" | "datasource" | "schema" | "anchor", target_uri: string, node_id?: string, metadata?: Record<string, unknown> }`. Resolution happens lazily at render time (e.g., document ref resolved when inspector section mounts). This is a forward declaration — 03 (anchor_refs) and 04 (datasource refs) populate specific ref_types. Initial implementation only needs the shape; resolution logic comes with each consuming step.

**What this absorbs from CvGraphEditor:**
- Container/group model → first-class graph_content concept
- Proxy edges → view-layer behavior driven by container state
- Typed payloads (entries, skills) → handled by schema + registry (01b)
- API persistence → generalized into pluggable persistence boundary
- Drag reorder → semantic action in graph_history

**Persistence boundary:** graph_content and external_refs are persistable. graph_view is session-local with optional named snapshots (→ 01a presets). graph_history is append-only, optionally persistable for audit. Persistence API is pluggable — localStorage for sandbox, REST API for production, neo4j adapter for graph database.

### 2. Objectives

1. Written state contract covers all four layers and accommodates container nesting
2. NodeEditor can represent everything CvGraphEditor currently does through the contract
3. Adding a new layout preset (01a) or node type (01b) does not require changing the state contract shape
4. Persistence boundary is explicit: what's saved, what's session-only, what's optional
5. zustand store replaces the current useState sprawl
6. Persistence API is pluggable (localStorage, REST, neo4j)

### 3. Don'ts

- **Don't persist graph_view by default.** View state is ephemeral. Named presets (01a) are the deliberate persistence mechanism.
- **Don't put annotation content in graph_content.** Annotations are references (external_refs), not graph nodes.
- **Don't implement container rendering here.** This step defines that containers exist in the data model. Rendering comes in 02.
- **Don't add undo/redo implementation here.** This step defines what actions are loggable. 01c defines undo/redo.
- **Don't design around CvGraphEditor's API shape.** Persistence API should be generic.

### 4. Known Gaps & Open Questions

- **GAP-ARCH-01** (Blocker → resolved here): No shared persistence boundary — this step defines it.
- **GAP-ARCH-02** (High → resolved here): No unified state contract — this step creates it.
- **GAP-IMPL-01** (High): NodeEditor has no save/load — persistence API addresses this.

### 5. Library Decision Matrix

**LIB-STATE-01**: zustand (committed). Smallest API surface, works outside React, devtools support, no provider boilerplate. Middleware for persistence (zustand/middleware persist) and undo (temporal or custom).

### 6. Test Plan

- **Unit**: State layer separation — graph_content mutation doesn't affect graph_view. Container nesting model (parent_id, child ordering). Pluggable persistence serialization/deserialization.
- **Component**: NodeEditor hydrates from a shared fixture including containers.
- **Integration**: Save graph → reload → state matches. Switch persistence adapter → same behavior.

### 7. Review Checklist

- [ ] State contract file exists with all four layers
- [ ] Container model in graph_content (parent_id, child ordering)
- [ ] Persistence boundary documented
- [ ] No graph_view in persistence
- [ ] zustand store replaces useState
- [ ] Pluggable persistence API defined

---

## Step 01a — Layout & View Presets

### 1. Architecture Logic

elkjs from the start. No dagre. Compound/nested layout natively supports containers (02) and document subflows without migration.

**Six preset types:**
- `dag_default` — elkjs layered algorithm, left-to-right
- `focus_centered` — concentric rings around a focal node
- `timeline_horizontal(property)` — sort by date/sequence on X axis
- `compare_lanes(left_prop, right_prop)` — two-column comparison
- `tree_top_down(root_rule)` — elkjs tree algorithm
- `manual_saved(name)` — user-positioned snapshot

**Saved view = preset + viewport + collapsed_state + filter_state + panel_layout (FlexLayout serialized state).** Persisted only when explicitly named.

**Each schema view can declare its default layout** — views that are subgraph queries get their own preset.

elkjs feeds React Flow directly. No abstraction layer.

### 2. Objectives

1. User can select a preset type and graph re-layouts via elkjs
2. User can name and save the current view (preset + viewport + filters + collapsed state + panel layout)
3. Reloading a saved view restores the full visual state
4. elkjs compound layout works with container/child relationships
5. Property-driven presets (timeline, compare) work with any attribute key
6. Schema views declare default layouts

### 3. Don'ts

- **Don't store node positions in graph_content.** Positions are view state.
- **Don't auto-save presets.** Explicit user action only.
- **Don't tune elkjs parameters per-graph.** Sensible defaults per preset type.
- **Don't keep dagre as fallback.** Full migration to elkjs.

### 4. Known Gaps & Open Questions

- **GAP-IMPL-03** (resolved here): Layout presets are local state only.
- Property-driven presets need attribute type awareness (which properties are dates? numbers?) — resolved by schema's attribute declarations.

### 5. Library Decision Matrix

**LIB-LAYOUT-01**: elkjs (committed). WASM worker for non-blocking layout. Handles compound, layered, tree, force algorithms in one library.

### 6. Test Plan

- **Unit**: Each preset type produces deterministic positions for a fixture graph. Compound layout respects parent-child containment. Save/restore round-trip preserves all view state fields. Property-driven preset: fixture graph with date attributes → `timeline_horizontal("created_at")` → nodes ordered by date on X axis.
- **Integration**: Apply preset → save → reload → viewport matches. Schema view declares layout → view loads with correct preset.

### 7. Review Checklist

- [ ] elkjs integrated, dagre removed
- [ ] All 6 preset types work
- [ ] Save/restore view works
- [ ] Compound layout handles containers
- [ ] Schema views declare default layouts
- [ ] No positions in graph_content

---

## Step 01b — Node Type Registry & Modes

### 1. Architecture Logic

The registry is populated from the representation schema's `node_types`. The editor ships with base renderers that the schema's `content_type` maps onto. No hardcoded node families.

**Registry shape:** Lookup table keyed by `type_id`. Each entry declares:
- `type_id`, `icon`, `category` — identity and visual grouping
- `payload_schema` — data shape (compiled from schema attributes)
- `renderers` — four modes: minimized, focus, edit_in_context, full_editor
- `supported_anchors` — annotation anchor types
- `default_size`, `allowed_relations` — layout and connection constraints
- `container_config` — if container: child ordering rules, collapse behavior, proxy edge style

**Base renderer set (built-in extensions):**
- entity (generic card with attributes)
- container (collapsible group with children)
- markdown_text (03b)
- code_block (03e)
- json_payload (03c)
- table (03d)
- image (03f)
- html_safe (sanitized embed)

**Two orthogonal axes:**
- **EditorState** (5 states, defined in 01 as part of graph_view, transitions governed by 01c's action taxonomy): `browse | focus | focus_relation | edit_node | edit_relation`
- **Renderer mode** (4 modes, per node type, chosen by dispatcher based on EditorState + node context): `minimized | focus | edit_in_context | full_editor`

The mapping from EditorState to renderer mode is contextual:
- `browse` → all nodes get `minimized`
- `focus` → focused node gets `focus`, others get `minimized`
- `edit_node` → focused node gets `edit_in_context` or `full_editor` (per type config), others get `minimized`
- `focus_relation` / `edit_relation` → focused endpoints get `focus`, others `minimized`

**Dispatcher:** One React Flow `nodeTypes` entry — reads registry by `type_id`, resolves renderer mode from current EditorState + node focus, delegates to correct renderer. Unknown types get fallback (generic card).

### 2. Objectives

1. All nodes render through registry lookup
2. Each registered type supports at least minimized + focus + full_editor
3. Adding a new type = schema entry + optional custom renderer extension. Zero editor shell changes.
4. Container is a first-class type with container_config
5. Fallback renderer handles unknown types gracefully
6. Schema's node_types populate the registry at load time

### 3. Don'ts

- **Don't implement all renderers at once.** Entity + container fully implemented. Others registered with fallback until 03-series.
- **Don't embed rich content rendering here.** Registry declares what a type needs. 03 implements renderers.
- **Don't skip the fallback renderer.** Unknown types must not crash.
- **Don't hardcode mode transitions in the registry.** Registry maps EditorState × node context → renderer mode. EditorState transitions live in 01c.
- **Don't couple payload_schema to a validator.** TypeScript discriminated unions now. Zod later if needed.

### 4. Known Gaps & Open Questions

- **GAP-ARCH-03** (High): Anchor identity model — declared here (`supported_anchors`), implemented in 03a.
- **GAP-DEP-01** (Blocker): This step MUST complete before any 03-series work.

### 5. Library Decision Matrix

No new libraries. React Flow's `nodeTypes` API is the integration surface.

### 6. Test Plan

- **Unit**: Registry lookup returns correct renderers for known types, fallback for unknown. container_config serialization.
- **Component**: Dispatcher renders minimized/focus/edit modes correctly. Unknown type gets fallback.
- **Integration**: Create container node → add child → collapse → proxy edges appear.

### 7. Review Checklist

- [ ] Registry populated from schema
- [ ] All nodes route through dispatcher
- [ ] Fallback renderer works
- [ ] Container type has container_config
- [ ] Adding new entry doesn't touch editor shell
- [ ] Entity + container fully rendered

---

## Step 01c — Editor State & History Contract

### 1. Architecture Logic

Unified action taxonomy covering all operations including container interactions from CvGraphEditor.

**Semantic action families (undoable):**
- Create / delete node
- Edit node payload (before/after snapshots)
- Create / delete relation
- Edit relation payload
- Attach / detach external reference
- Create / delete annotation anchor
- Reorder within container
- Move node between containers
- Collapse / expand container (borderline — included because it affects proxy edge rendering)

**View-only actions (NOT undoable):**
- Pan / zoom / fit view
- Apply layout preset
- Toggle visibility filters
- Selection changes

**Action metadata:** `actor`, `timestamp`, `affected_ids`, `undo_payload`, `redo_payload`.

**Dirty detection:** Action-count-since-last-save replaces JSON-snapshot comparison.

**Integration:** History stack in zustand store. All mutations through `dispatch(action)`.

### 2. Objectives

1. All graph mutations use the semantic action taxonomy
2. Undo/redo works for all undoable action types including container operations
3. View-only actions never appear in the history stack
4. Dirty detection is action-count-based
5. Action log can be inspected (devtools or sidebar)

### 3. Don'ts

- **Don't log view actions.** Pan/zoom are high-frequency. Bloats stack.
- **Don't implement collaborative conflict resolution.** Single-user only.
- **Don't couple action format to persistence format.** History is in-memory. Persistence saves resulting state.
- **Don't make undo cross-context.** Each graph document gets its own stack.

### 4. Known Gaps & Open Questions

Container operations need to be added to the existing 4-kind HistoryAction. This is new implementation.

### 5. Library Decision Matrix

No new libraries. Zustand middleware for undo/redo stack management. Immer optional for snapshot ergonomics.

### 6. Test Plan

- **Unit**: dispatch create → undo → state matches original. View-only action doesn't change history length. Dirty counter increments on semantic action, resets on save. Container reorder → undo → original order.
- **Component**: Ctrl+Z triggers undo, UI updates.
- **Integration**: create → edit → undo → undo → state is empty.

### 7. Review Checklist

- [ ] Action taxonomy covers all operations including containers
- [ ] Undo/redo works
- [ ] View actions excluded from history
- [ ] Dirty detection is action-based
- [ ] No cross-context undo leaks

---

## Step 02 — Structured Documents & Subflows

### 1. Architecture Logic

Containers compose to represent documents: document → section → block (3-level cap). Uses React Flow's `parentId` + `extent: "parent"` directly for rendering. elkjs compound layout for positioning.

**Nesting model:**
```
Document (container)
  └─ Section (container)
      └─ Block (leaf or container)
          └─ Inline anchor / reference
```

**Each container supports:**
- Collapsed summary (child count, title, status)
- Expanded view (children laid out by elkjs)
- Explicit child ordering (order array, not position-derived)
- Proxy edges when collapsed (dashed, deduplicated)
- Depth limit per view preset

**Structural interactions:**
- Absorption — drag node onto container
- Extraction — drag child out
- Reorder — drag within container (updates order array)
- Cross-container move — drag between containers

All four are semantic actions (01c) — fully undoable.

### 2. Objectives

1. 3-level nesting works (document → section → block)
2. Collapse/expand with correct proxy edges
3. All drag interactions work and are undoable
4. elkjs compound layout produces correct nested positioning
5. Child ordering is explicit (order array)
6. Nesting depth capped per view preset

### 3. Don'ts

- **Don't allow infinite nesting.** Default cap at 3 levels. Configurable per schema via `max_nesting_depth` field (default 3).
- **Don't derive order from Y position.** Order array is truth.
- **Don't render all levels simultaneously.** Progressive expansion.
- **Don't implement content rendering here.** Nesting model only. Content is 03's territory.
- **Don't create a separate "document mode."** Documents are graphs with containers.

### 4. Known Gaps & Open Questions

Proxy edge deduplication logic needs generalization. Performance with many collapsed containers untested.

### 5. Library Decision Matrix

elkjs (already adopted), React Flow parentId/extent (built-in). No new libraries.

### 6. Test Plan

- **Unit**: Order array mutation produces correct sequence. Proxy edge computation on collapse/expand. Cross-container move updates both order arrays.
- **Component**: Drag onto container → absorption feedback → child appears inside.
- **Integration**: Build 3-level doc → collapse all → expand selectively → proxy edges correct.

### 7. Review Checklist

- [ ] 3-level nesting works
- [ ] All drag interactions undoable
- [ ] Proxy edges correct
- [ ] Order array is source of truth
- [ ] elkjs handles compound layout

---

## Step 02a — Tree Mode & Outline Sync

### 1. Architecture Logic

Sidebar tree panel derived from graph_content's container relationships. No separate data model. Bidirectional sync with canvas.

**Sync contract:**
- Selection: tree click → canvas focus. Canvas click → tree highlight.
- Expand/collapse: syncs both directions.
- Drag reorder in tree → dispatches same semantic action as canvas.
- Cross-container drag in tree → same as canvas.

**Placement:** Sidebar panel extension via FlexLayout. Dockable left/right/float.

**Per item:** Node icon (from registry), label, child count badge, type indicator. No payload preview.

### 2. Objectives

1. Tree reflects container hierarchy from graph_content
2. Bidirectional selection sync
3. Bidirectional expand/collapse sync
4. Drag reorder in tree is undoable
5. Tree updates reactively on graph_content changes
6. Tree is a dockable sidebar panel (FlexLayout)

### 3. Don'ts

- **Don't create a separate tree data model.** graph_content IS the tree.
- **Don't show non-hierarchical edges in tree.** Containment only.
- **Don't add content preview.** Tree is for navigation.
- **Don't make tree required.** Optional panel.
- **Don't implement tree-only mutations.** Same semantic actions as canvas.

### 4. Known Gaps & Open Questions

Performance at 200+ nodes — react-arborist handles virtualization but needs testing.

### 5. Library Decision Matrix

**LIB-TREE-01**: react-arborist (committed). Built-in virtualization, drag-drop, keyboard nav, controlled mode.

### 6. Test Plan

- **Unit**: Tree derivation from graph_content produces correct hierarchy.
- **Component**: Click tree item → onFocus fires. Drag reorder → dispatches action.
- **Integration**: Create nested structure → open tree → select → canvas focuses → collapse in tree → canvas collapses.

### 7. Review Checklist

- [ ] Tree derives from graph_content
- [ ] Selection sync both directions
- [ ] Expand/collapse sync both directions
- [ ] Drag dispatches semantic actions
- [ ] Tree is optional FlexLayout panel

---

## Step 03 — Rich Content Nodes (Shared Contract)

### 1. Architecture Logic

Bridge between node type registry (01b) and specific content renderers (03a–03f). Defines the shared payload and rendering contract.

**Rich node payload contract:**
- `content_type` — discriminant matching registry type_id
- `payload` — actual content (markdown string, JSON object, image ref, etc.)
- `anchor_refs[]` — annotation anchors attached to ranges within content
- `external_asset_refs[]` — pointers to external files, URLs, schema entries
- `edit_capabilities` — what this content type supports: inline edit, full editor, read-only, format-on-save

**Renderer contract:** Each content type provides a React component per mode (as a node_renderer extension). Commits changes through `dispatch(edit_node_payload)`.

**Anchor attachment model:** Rich content can have internal anchors (text range, line range, image region, key path). Content-type-specific selectors stored in `anchor_refs`.

### 2. Objectives

1. Shared payload contract exists as TypeScript interface
2. All 03a–03f types implement it without editor special-casing
3. Anchor model supports content-type-specific selectors
4. Edits flow through dispatch(edit_node_payload)
5. Persistence handles all payload types through one path

### 3. Don'ts

- **Don't let content renderers manage own persistence.** Commit through dispatch.
- **Don't define anchor selectors for unimplemented types.** Each 03x step defines its own.
- **Don't embed display_mode in persisted payload.** display_mode is view state.
- **Don't create abstract base classes.** Interface + discriminated union.

### 4. Known Gaps & Open Questions

- **GAP-ARCH-03** (resolved here): Anchor identity model defined.

### 5. Library Decision Matrix

None. Contract definition step.

### 6. Test Plan

- **Unit**: Each content type payload serializes/deserializes correctly. Anchor_refs survive payload edits. TypeScript exhaustiveness check.

### 7. Review Checklist

- [ ] Contract interface exists
- [ ] All 03x types can implement it
- [ ] Anchor model supports multiple selectors
- [ ] display_mode not in persisted payload
- [ ] Single dispatch path

---

## Step 03a — Text Annotation Links

### 1. Architecture Logic

Reusable anchor model for text spans across any text-bearing content type. RichTextPane's patterns inform the design; built fresh for the graph context.

**Anchor model:**
- `document_ref` — which node's payload contains the text
- `anchor_id` — unique identifier
- `selector_type` — offset_range | line_range | quote | block_id
- `selector_payload` — type-specific data
- `linked_node_ids[]` — graph nodes this anchor connects to
- `confidence` — validity likelihood after text edits (1.0 = exact, degrades)

**Lifecycle:** Select text → create anchor → link to nodes → on text edit: recompute offsets, degrade confidence if content changed → below threshold: mark stale.

### 2. Objectives

1. Nodes can attach to text anchors in any text-bearing content
2. Content-type-appropriate selectors (offset for text, line for code)
3. Anchors survive normal edits with confidence tracking
4. Stale anchors visually flagged, not silently dropped
5. Creating an anchor is undoable

### 3. Don'ts

- **Don't silently delete stale anchors.** Flag them.
- **Don't store anchor content as a copy.** Anchor is a pointer.
- **Don't build CRDT-style tracking.** Simple offset shift + quote matching.
- **Don't couple to RichTextPane's category system.** Anchor model is generic.

### 4–7: Gaps, Libraries, Tests, Review

See consolidated matrices in 00_gap_matrix.md and 00_library_decisions.md. Tests: anchor offset shift on insertion, confidence degradation on deletion, quote selector after surrounding edits, create/undo cycle.

---

## Steps 03b–03f — Rich Content Renderers

Each follows the same template. Key details:

### 03b — Markdown Formatted Editor
- Split source/preview, no WYSIWYG. Markdown is source of truth.
- Anchors reference source offsets. Debounced commit.
- Libraries: decision matrix (Lexical vs Tiptap vs CodeMirror markdown mode) + rendering lib (marked or remark+rehype).

### 03c — JSON/YAML Views
- Stored as parsed object, not raw string. Collapsible tree inspector (focus), validated text edit (edit).
- JSON↔YAML toggle is display-only. Key-path anchors.
- Libraries: decision matrix (@uiw/react-json-view vs react-inspector) + CodeMirror for edit mode.

### 03d — Table Editor
- Typed columns, inline cell editing, add/remove row/column. No spreadsheet parity.
- Cell coordinate anchors. Structured object storage.
- Libraries: TanStack Table (recommended) vs AG Grid.

### 03e — Code Display & Annotation
- Syntax highlighting, line-range anchors with gutter markers. Optional editing + explicit format-on-save.
- Libraries: CodeMirror 6 (recommended) vs Monaco. No LSP.

### 03f — Image Annotation
- Rectangle regions with normalized coordinates (0-1). Images as external asset references.
- Libraries: decision matrix (Annotorious vs react-image-annotate).

### html_safe — Sanitized HTML Rendering
- Renders sanitized HTML within nodes. Used for embedded HTML snippets from external sources.
- **Sanitization strategy:** DOMPurify with restrictive tag allowlist (no `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`). Allowed tags: semantic HTML (`<h1>`–`<h6>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<tr>`, `<td>`, `<th>`, `<span>`, `<div>`, `<a>`, `<img>`, `<code>`, `<pre>`, `<blockquote>`). Attributes stripped except `class`, `id`, `href`, `src`, `alt`.
- **CSP:** Inline styles stripped. All styling via CSS classes that the theme can target.
- **Fallback:** If sanitization removes >50% of input HTML, show a warning with "View raw source" option.
- No anchoring support (HTML structure too variable). Read-only display mode only.
- Libraries: DOMPurify (committed — standard, well-maintained).

---

## Step 04 — External Data & Schema Integration

### 1. Architecture Logic

Source adapter system driven by schema's `sources` section. Adapters ingest external data into neo4j as canonical base.

**Adapter types:** neo4j (direct), json_file (read + MERGE), api (fetch + MERGE), yaml_file.

**Pipeline:** Schema declares sources → adapter reads → maps to MERGE commands → executes against neo4j → provenance metadata attached.

**View query execution:** Subgraph views execute Cypher against neo4j, return graph_content for editor.

**Lazy loading:** Views declare `load_attributes`. Attributes not listed aren't fetched.

### 2. Objectives

1. neo4j + json_file adapters work end-to-end
2. MERGE semantics (idempotent)
3. Provenance metadata on all ingested nodes
4. Subgraph view queries execute correctly
5. Lazy attribute loading respects load_attributes
6. Adapter registry is extensible (source_adapter extension type)

### 3. Don'ts

- **Don't build bidirectional sync.** Ingestion is one-way.
- **Don't execute arbitrary Cypher from UI.** View queries are schema-declared.
- **Don't fetch all attributes upfront.** Respect load_attributes.
- **Don't couple adapters to each other.** Cross-source joins happen in neo4j.
- **Don't reinvent ETL.** Adapters are thin: read, map, MERGE.

### 4–7: See consolidated annexes.

---

## Step 04a — Document Explorer

### 1. Architecture Logic

Project-level navigation: schemas, views, graph outline, assets, saved presets. One active schema at a time. Selection drives the editor.

**Sections:** Schemas list, Views list, Graph outline (02a embedded), Assets browser, Saved presets.

**Placement:** Left sidebar panel (FlexLayout). Tree from 02a is one section within.

### 2. Objectives

1. Explorer lists schemas and views
2. View selection triggers correct load
3. Outline embedded as section
4. Assets browseable and linked to nodes
5. Saved presets accessible

### 3. Don'ts

- **Don't build a file manager.** Schema-declared assets only.
- **Don't load all schemas simultaneously.** One active at a time.
- **Don't duplicate the tree.** 02a is a section within explorer.

### 4–7: See consolidated annexes.

---

## Step 05 — Validation & Test Impact Map

### 1. Architecture Logic

Operational contract. Every implementation task declares its impact dimensions before coding.

**Impact dimensions:** State contracts, persistence, rendering, interaction, schema, theme.

**Verification matrix:**

| If you change... | Verify... |
|---|---|
| State contract | All views load. Undo/redo. Save/load round-trip. |
| Schema format | All schemas parse. Editor loads. Views execute. |
| Node renderer | All 4 modes. Fallback works. Theme data-* present. |
| Container behavior | Collapse/expand. Proxy edges. Drag interactions. Tree sync. |
| Anchor model | Creation. Edit survival. Stale detection. Undo. |
| Data ingestion | MERGE correct. Idempotent. Provenance. View queries. |
| CSS theme | Default renders all types. Overrides apply. No unstyled elements. |
| Extension | Registration works. Activation rules correct. Mount/unmount clean. |

### 2. Objectives

1. Every PR references impact dimensions
2. Tests organized by impact dimension
3. Regression risk bounded before coding
4. Map maintained as living document

### 3. Don'ts

- **Don't treat as optional.** It's a gate.
- **Don't organize tests by file path only.** Impact-based groups.
- **Don't let it go stale.** Update with every step.

### 4. Known Gaps & Open Questions

- **GAP-IMPL-02** (High): Zero frontend test files currently exist. Bootstrap required.

### 5. Library Decision Matrix

N/A — uses Vitest + @testing-library/react + Playwright (all committed).

### 6. Test Plan

- **Unit**: Impact dimension map is complete (all steps covered). Each dimension has at least one verification entry.
- **Component**: Test runner config works, sample test passes.
- **Integration**: Full CI pipeline runs all test suites.

### 7. Review Checklist

- [ ] Verification matrix covers all impact dimensions
- [ ] Every PR template includes impact dimension field
- [ ] Tests are organized by impact dimension
- [ ] Map is updated with each new step implementation
- [ ] Test infrastructure (Vitest + Testing Library + Playwright) bootstrapped and passing

---

## Consolidated Gap Matrix

| ID | Category | Severity | Steps | Description | Resolution |
|---|---|---|---|---|---|
| GAP-ARCH-01 | Architecture | Blocker | 01 | No persistence boundary | Resolved in 01 |
| GAP-ARCH-02 | Architecture | High | 01 | No unified state contract | Resolved in 01 |
| GAP-ARCH-03 | Architecture | High | 01b, 03, 03a | No anchor identity model | Declared in 01b, implemented in 03 |
| GAP-IMPL-01 | Implementation | High | 01 | NodeEditor has no save/load | Resolved in 01 (pluggable persistence) |
| GAP-IMPL-02 | Implementation | High | all | Zero frontend test files | Resolved in 00 test infrastructure |
| GAP-IMPL-03 | Implementation | Medium | 01a | Layout presets local-only | Resolved in 01a |
| GAP-DEP-01 | Dependency | Blocker | 03a-f | Rich nodes before registry | 01b must complete first |
| GAP-DEP-02 | Dependency | High | 04, 04a | External data before persistence | 01 must complete first |
| GAP-SCHEMA-01 | Schema | Medium | 00c | Schema evolution / versioning | schema_version + migration functions |
| GAP-SCHEMA-02 | Schema | Medium | 00c | Cross-schema views | Define merged schema or cross-refs |
| GAP-SCHEMA-03 | Schema | Low | 00c | Schema inheritance | Deferred |
| GAP-THEME-01 | Theme | Medium | 00d | Dark mode strategy | Theme files use media queries |
| GAP-THEME-02 | Theme | Low | 00d | Theme validation warnings | Dev-mode console warnings |
| GAP-EXT-01 | Extension | Medium | 00e | Extension packaging | Deferred until first external consumer |
| GAP-EXT-02 | Extension | Low | 00e | Extension conflict resolution | Last-registered wins + warning |
| GAP-PERF-01 | Performance | Medium | 02 | Proxy edge deduplication untested at scale | Generalize dedup logic, benchmark with 20+ collapsed containers |
| GAP-PERF-02 | Performance | Medium | 01, 01a | No performance budget for large graphs (500+ nodes) | Set target: layout <500ms, render <16ms. elkjs WASM worker helps but needs benchmark |
| GAP-SPEC-01 | Spec | Medium | — | Two critical docs in Spanish only: `plan/ui/node_editor_frontend_implementation_plan.md` and `plan/ui/cv_graph_container_nodes_uiux_spec.md` | Translate or create English summaries |

---

## Consolidated Library Decisions

| ID | Decision | Recommendation | Switch Trigger |
|---|---|---|---|
| LIB-STATE-01 | State management | zustand | N/A — committed |
| LIB-LAYOUT-01 | Layout engine | elkjs | N/A — committed, replaces dagre |
| LIB-DOCK-01 | Dockable panels | FlexLayout-react | CSS impossible to align with MD3 |
| LIB-FORMS-01 | Schema-driven forms | RJSF (@rjsf/core) | Custom widget API too limited |
| LIB-TREE-01 | Explorer tree | react-arborist | Sync contract impossible |
| LIB-NEO4J-01 | Graph database driver | neo4j-driver | N/A — official driver |
| LIB-TEST-01 | Unit/component testing | Vitest + @testing-library/react | N/A — committed |
| LIB-E2E-01 | Integration testing | Playwright | N/A — already in use |
| LIB-RICHTEXT-01 | Markdown editor | TBD (matrix in 03b) | — |
| LIB-CODE-01 | Code editor | CodeMirror 6 (recommended) | IDE-grade features justify Monaco |
| LIB-JSON-01 | JSON/YAML inspector | TBD (matrix in 03c) | — |
| LIB-TABLE-01 | Table editor | TanStack Table (recommended) | Spreadsheet-grade features justify AG Grid |
| LIB-IMAGE-01 | Image annotation | TBD (matrix in 03f) | — |
