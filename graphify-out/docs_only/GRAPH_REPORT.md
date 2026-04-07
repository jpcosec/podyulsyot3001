# Graph Report - docs  (2026-04-06)

## Corpus Check
- 13 files · ~39,882 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 46 nodes · 112 edges · 9 communities detected
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Unified Automation Refactor Design Spec` - 12 edges
2. `Automation Architecture` - 11 edges
3. `Unified Automation Migration Implementation Plan` - 10 edges
4. `Ariadne portal schema` - 10 edges
5. `Ingestion Layer Standards` - 9 edges
6. `Documentation index` - 7 edges
7. `Documentation & Planning Guide` - 7 edges
8. `Basic Code Standards` - 7 edges
9. `Crawl4AI Usage Standard` - 7 edges
10. `Structural migration` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Unified Automation Refactor Design Spec` --semantically_similar_to--> `Automation Architecture`  [INFERRED] [semantically similar]
  docs/superpowers/specs/2026-04-06-unified-automation-refactor-design.md → docs/automation/architecture.md
- `Five-step feature and refactor methodology` --conceptually_related_to--> `Structural migration`  [INFERRED]
  docs/standards/feature_creation_methodology.md → docs/unified_automation_gap_analysis.md
- `Unified Automation Refactor Design Spec` --semantically_similar_to--> `Unified Automation Migration Implementation Plan`  [INFERRED] [semantically similar]
  docs/superpowers/specs/2026-04-06-unified-automation-refactor-design.md → docs/superpowers/plans/2026-04-06-unified-automation-migration.md
- `Feature Creation & Refactor Methodology` --conceptually_related_to--> `Unified Automation Migration Implementation Plan`  [INFERRED]
  docs/standards/feature_creation_methodology.md → docs/superpowers/plans/2026-04-06-unified-automation-migration.md
- `Unified Automation Refactor Design Spec` --defines--> `Unified automation system`  [EXTRACTED]
  docs/superpowers/specs/2026-04-06-unified-automation-refactor-design.md → docs/automation/README.md

## Communities

### Community 0 - "Community 0"
Cohesion: 0.54
Nodes (8): Documentation lifecycle rules, Docs as navigation layer, Ephemeral plan lifecycle, README contract, Documentation & Planning Guide, Documentation Quality Checklist, Documentation index, Documentation should point to code rather than duplicate code details

### Community 1 - "Community 1"
Cohesion: 0.62
Nodes (7): Crawl4AI extraction lifecycle, LLM extraction as last resort, Non-LLM extraction as default, Saved schema first, LLM second, Crawl4AI Custom LLM Context, Crawl4AI Usage Standard, Steady-state scraping should prefer deterministic saved schemas over LLM extraction

### Community 2 - "Community 2"
Cohesion: 0.57
Nodes (7): Ariadne portal schema, Execution mechanics, Motor separation, Portal knowledge, Automation Architecture, Adding a new execution backend should not require changing portal intent files, Mechanisms, domain knowledge, state, and orchestration should evolve independently

### Community 3 - "Community 3"
Cohesion: 0.6
Nodes (6): Validation at the boundary, Idempotent ingestion, Ingestion contract, LLM rescue fallback pattern, Ingestion Layer Standards, All external input should be validated at the ingestion boundary before downstream use

### Community 4 - "Community 4"
Cohesion: 0.87
Nodes (6): BrowserOS CLI motor, Crawl4AI motor, Portal intent files, Unified automation CLI, Unified Automation Migration Implementation Plan, Unified Automation Refactor Design Spec

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (4): Module structure standard, Boundary data contracts, LogTag observability discipline, Basic Code Standards

### Community 6 - "Community 6"
Cohesion: 0.83
Nodes (4): Migration gap inventory, Phase 2 deferred work, Structural migration, Unified Automation Gap Analysis

### Community 7 - "Community 7"
Cohesion: 1.0
Nodes (2): Unified automation system, Automation System document

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (2): Five-step feature and refactor methodology, Feature Creation & Refactor Methodology

## Knowledge Gaps
- **Thin community `Community 7`** (2 nodes): `Unified automation system`, `Automation System document`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 8`** (2 nodes): `Five-step feature and refactor methodology`, `Feature Creation & Refactor Methodology`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Automation Architecture` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.414) - this node is a cross-community bridge._
- **Why does `Documentation index` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.253) - this node is a cross-community bridge._
- **Why does `Unified Automation Refactor Design Spec` connect `Community 4` to `Community 2`, `Community 5`, `Community 6`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Unified Automation Refactor Design Spec` (e.g. with `Unified Automation Migration Implementation Plan` and `Automation Architecture`) actually correct?**
  _`Unified Automation Refactor Design Spec` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Unified Automation Migration Implementation Plan` (e.g. with `Unified Automation Refactor Design Spec` and `Feature Creation & Refactor Methodology`) actually correct?**
  _`Unified Automation Migration Implementation Plan` has 2 INFERRED edges - model-reasoned connections that need verification._