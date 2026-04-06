# Automation Asset Placement

Status: **completed** — migration executed 2026-04-06. All decisions below were resolved. Retained as design context.

This document answered: for each asset type, where should it live in the target automation architecture?

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
data/ariadne/reference_data/applying_traces/   # screenshots, exploratory evidence, walkthrough artifacts
<automation-package>/ariadne/traces/            # normalized packaged replay paths used by runtime code
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

### 4. Planning and design docs

Active planning docs live in `plan_docs/automation/`, grouped by concern:

- `plan_docs/automation/ariadne/`
- `plan_docs/automation/browseros/`
- `plan_docs/automation/crawl4ai/`
- `plan_docs/automation/migration/`

Note: earlier references to `plan_docs/issues/` and `docs/reference/external_libs/` pointed to
paths that do not exist in this worktree. Those paths belonged to the full repo before worktree
scoping and should not be treated as current sources.

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
| Exploratory screenshot trace | `data/ariadne/reference_data/applying_traces/xing/*.png` | `data/ariadne/reference_data/applying_traces/` (stays in data, not plan_docs) |
| Crawl4AI schema cache | `data/ariadne/assets/crawl4ai_schemas/*` | temporary home; target is Crawl4AI motor-local `schemas/` or runtime cache (see section 3) |
| Planning/design doc | `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md` | `plan_docs/automation/...` |

## Migration gate

Before code moves begin, every moved asset should be classified using this document.

If an asset cannot be classified cleanly as:

- runtime code
- packaged runtime asset
- docs/reference artifact
- runtime data/cache

then its destination is not clear enough yet and the move should pause.
