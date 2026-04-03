# Automation Asset Placement

Status: pre-migration reference for deciding where existing assets go before code moves.

This document answers a simple question: for each current asset type, where should it live in the target automation architecture?

## Decision rules

Use these rules before moving anything:

1. If the asset is runtime code, it belongs under the future automation package.
2. If the asset is a packaged runtime replay asset, it belongs under the future Ariadne package.
3. If the asset is exploratory evidence or design reference, it belongs under `plan_docs/automation/` while it remains planning material.
4. If the asset is motor-specific implementation data, it belongs under that motor, not Ariadne.
5. If the asset is operator/runtime state, it belongs under `data/`, not in source docs or code.

## Existing asset groups

### 1. `data/ariadne/reference_data/applying_traces/`

Current meaning:

- mixed design/reference evidence
- screenshots from portal walkthroughs
- at least one JSON trace/playbook used as a design-time source

Target placement rule:

- screenshots and exploratory traces stay in docs
- normalized packaged replay paths move into Ariadne runtime assets

Recommended split:

```text
plan_docs/automation/ariadne/traces/    # screenshots, exploratory evidence, walkthrough artifacts
<automation-package>/ariadne/traces/    # normalized packaged replay paths used by runtime code
```

Concrete implication:

- `data/ariadne/reference_data/applying_traces/linkedin_easy_apply/playbook_linkedin_easy_apply_v1.json`
  - if it remains a reference/source artifact, keep it under docs
  - if it becomes the canonical packaged replay path, move/copy the normalized form under the packaged Ariadne trace area

### 2. Current packaged playbooks in code

Current example:

- `src/apply/playbooks/linkedin_easy_apply_v1.json`

Target placement:

- the packaged Ariadne trace area

Reason:

- packaged replay paths are Ariadne assets, not BrowserOS-only assets

### 3. `data/ariadne/assets/crawl4ai_schemas/`

Current meaning:

- Crawl4AI extraction schema cache/reference files
- scraper-specific deterministic extraction assets

Target placement:

- under the Crawl4AI motor, not under Ariadne and not under docs if they are runtime assets

Recommended destination options:

- shipped with code: a Crawl4AI motor-local `schemas/` folder
- generated at runtime: `data/runtime/crawl4ai/schemas/` or another runtime-owned cache path

Decision rule:

- if the schema is part of the repository and used as source-controlled runtime configuration, keep it in code under the Crawl4AI motor
- if it is generated per environment and should not be source-controlled, move it to a runtime data/cache path

### 4. Existing apply planning docs

Current examples:

- `plan_docs/issues/apply/applying_feature_design.md`
- `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md`
- `docs/reference/external_libs/browseros_interfaces.md`
- `plan_docs/issues/scraper/scraper_fragility.md`

Target placement:

- `plan_docs/automation/`
- grouped by concern over time:
  - `plan_docs/automation/ariadne/`
  - `plan_docs/automation/browseros/`
  - `plan_docs/automation/crawl4ai/`
  - `plan_docs/automation/migration/`

Reason:

- these are documentation and planning references, not runtime code assets

### 5. Existing repo maps

Current files:

- `docs/repo_maps/current_repo_scrape_apply_browseros_ariadne_map.md`
- `docs/repo_maps/worktree_feat_apply_module_map.md`

Target placement:

- these can stay where they are as inventory docs, or later be linked from `plan_docs/automation/README.md`

Reason:

- they document the current and worktree states; they are migration reference material

### 6. Future Ariadne recordings from BrowserOS agent/CLI

Target placement flow:

- raw recording/debug output -> docs or runtime temp storage
- normalized approved recording -> the packaged Ariadne trace area if shipped with code
- job/session-specific runtime trace -> `data/jobs/<source>/<job_id>/nodes/ariadne/`

This gives a clean separation between:

- exploratory evidence
- packaged canonical paths
- per-job runtime artifacts

## Data-plane placement

Recommended job runtime layout after migration:

```text
data/jobs/<source>/<job_id>/nodes/
  ingest/
  apply/
  ariadne/
```

Where:

- `ingest/` = scrape/discovery artifacts
- `apply/` = apply execution artifacts
- `ariadne/` = per-job normalized traces, branch decisions, replay metadata, path-resolution output

## Quick classification table

| Asset type | Example now | Target home |
|---|---|---|
| Scrape runtime code | `src/scraper/smart_adapter.py` | Crawl4AI motor + portals area |
| Apply runtime code | `src/apply/smart_adapter.py` | Crawl4AI motor + portals area |
| BrowserOS runtime code | `src/apply/browseros_client.py` | BrowserOS CLI motor |
| Ariadne packaged path | `src/apply/playbooks/linkedin_easy_apply_v1.json` | packaged Ariadne trace area |
| Exploratory screenshot trace | `data/ariadne/reference_data/applying_traces/xing/*.png` | `data/ariadne/reference_data/applying_traces/` |
| Crawl4AI schema cache | `data/ariadne/assets/crawl4ai_schemas/*` | Ariadne assets for now; later a Crawl4AI motor-local `schemas/` folder or runtime cache |
| Planning/design doc | `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md` | `plan_docs/automation/...` |
| External library reference | `docs/reference/external_libs/browseros_interfaces.md` | `docs/reference/external_libs/` |

## Migration gate

Before code moves begin, every moved asset should be classified using this document.

If an asset cannot be classified cleanly as:

- runtime code
- packaged runtime asset
- docs/reference artifact
- runtime data/cache

then its destination is not clear enough yet and the move should pause.
