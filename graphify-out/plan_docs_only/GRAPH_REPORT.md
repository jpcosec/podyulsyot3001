# Graph Report - plan_docs  (2026-04-06)

## Corpus Check
- 33 files · ~26,948 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 96 nodes · 227 edges · 9 communities detected
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Unified Automation Refactor Plan` - 14 edges
2. `AriadneTarget` - 14 edges
3. `Ariadne Common Language - Open Issues Before Phase 2` - 13 edges
4. `Recording pipeline` - 13 edges
5. `Unified automation package` - 12 edges
6. `Ariadne path knowledge system` - 12 edges
7. `Automation Directory Glossary` - 11 edges
8. `BrowserOS CLI motor` - 10 edges
9. `BrowserOS Agent motor` - 10 edges
10. `Crawl4AI motor` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Stage 1 - Baseline and Inventory` ----> `data/jobs/<source>/<job_id>/nodes layout`  [INFERRED]
  plan_docs/planning/stage1_baseline.md → plan_docs/automation/asset_placement.md
- `Vision Motor - Placeholder` ----> `AriadneTarget`  [EXTRACTED]
  plan_docs/motors/vision.md → plan_docs/ariadne/common_language.md
- `OS Native Tools Motor - Placeholder` ----> `AriadneTarget`  [EXTRACTED]
  plan_docs/motors/os_native_tools.md → plan_docs/ariadne/common_language.md
- `Avoid building the full framework before proving the narrow path works end to end` ----> `Unified automation package`  [EXTRACTED]
  plan_docs/automation/round_1_gpt.md → plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md
- `Portal knowledge separated from execution backends` ----> `Portals as source-specific knowledge packages`  [EXTRACTED]
  plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md → plan_docs/contracts/portals.md

## Communities

### Community 0 - "Community 0"
Cohesion: 0.2
Nodes (18): Agent session contracts, BrowserOS Agent motor, CorrelatedStep, Human motor, Human session contracts, NormalizationResult, Normalize on capture, RawRecordingEvent (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.21
Nodes (17): Common automation CLI entrypoint, Unified automation package, NativePlan and NativeAction, OS native tools motor, Portal knowledge separated from execution backends, Vision motor, VisionQuery and VisionMatch, OS Native Tools Motor Contracts (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.32
Nodes (15): AriadnePath, AriadneStep, AriadneTarget, Backend-neutral common language, dry_run_stop checkpoint, Fallback semantics in common language, human_required gate, Intent vocabulary (+7 more)

### Community 3 - "Community 3"
Cohesion: 0.21
Nodes (12): BrowserOS CLI motor, BrowserOSCliPlan, Crawl4AI translator as compiler, Crawl4AI motor, CrawlPlan, Documentation-first phase order, BrowserOS CLI Motor Contracts, Crawl4AI Motor Contracts (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.38
Nodes (11): Asset classification before migration, data/jobs/<source>/<job_id>/nodes layout, Packaged canonical traces, Path promotion lifecycle, Runtime recordings and replay metadata, Ariadne storage model, Verification replay, Ariadne Path Promotion (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.33
Nodes (9): Ariadne path knowledge system, Deterministic translator, Backend-neutral error taxonomy, Ariadne Error Taxonomy, Ariadne - Path Knowledge System, Ariadne Translators, Gemini Agent Critical Analysis of plan_docs, Detailed planning docs risk becoming stale if not converted into code quickly (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.67
Nodes (7): ApplicationRecord, ExecutionContext, ExecutionResult, IngestArtifact, JobPosting, Shared cross-boundary contracts, Shared Contracts

### Community 7 - "Community 7"
Cohesion: 0.47
Nodes (6): PortalDefinition contract, Portal routing configuration, Portals as source-specific knowledge packages, Baseline inventory and issue audit, Portal Contracts, Stage 1 - Baseline and Inventory

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (1): Superpowers Folder Audit

## Knowledge Gaps
- **2 isolated node(s):** `Superpowers Folder Audit`, `Baseline inventory and issue audit`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 8`** (1 nodes): `Superpowers Folder Audit`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ariadne path knowledge system` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `BrowserOS Agent motor` connect `Community 0` to `Community 1`, `Community 2`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `Unified Automation Refactor Plan` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **What connects `Superpowers Folder Audit`, `Baseline inventory and issue audit` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._