# Ariadne Storage

Date: 2026-04-05
Status: design-only

## Purpose

Define where Ariadne paths live on disk, how they're versioned, and how they're
named. Storage is the persistence layer for everything Ariadne knows.

## Two storage locations

### 1. Packaged paths — ship with code

Canonical, production-ready paths that are source-controlled and distributed with
the automation package.

```
<automation-package>/ariadne/traces/
  linkedin/
    easy_apply/
      standard_v1.json
      standard_v2.json
  xing/
    standard_apply/
      standard_v1.json
  stepstone/
    quick_apply/
      standard_v1.json
```

**Current equivalent:** `src/apply/playbooks/linkedin_easy_apply_v1.json`

These are the paths that deterministic motors (Crawl4AI, BrowserOS CLI) load
for production apply runs. They have status `canonical`.

### 2. Runtime paths — per-job and per-session artifacts

Paths generated during recording sessions and per-job replay metadata. These
live in the data plane, not in source-controlled code.

```
data/ariadne/
  recordings/
    <session_id>/
      raw_timeline.jsonl         # raw recording events
      normalized_path.json       # AriadnePath (draft or verified)
      screenshots/               # evidence captured during recording
      session_meta.json          # who, when, which motor, which portal
  jobs/
    <source>/<job_id>/
      replay_meta.json           # which path was used, replay result
      replay_screenshots/        # evidence captured during replay
```

And per-job replay metadata also integrates with the existing data plane:

```
data/jobs/<source>/<job_id>/nodes/ariadne/
  replay_meta.json
  path_resolution.json           # which path was selected and why
```

### 3. Reference data — exploratory evidence (existing)

Not managed by Ariadne storage code. Pre-existing location for exploratory
screenshots and design-time traces:

```
data/ariadne/reference_data/applying_traces/
  linkedin_easy_apply/
  xing_apply/
```

This stays as-is. Ariadne storage manages packaged paths and runtime paths only.

Classification rule:

- exploratory screenshots and design traces stay in `data/ariadne/reference_data/`
- packaged canonical replay assets ship with code
- per-job and per-session runtime artifacts live under `data/ariadne/` or `data/jobs/.../nodes/ariadne/`

## Path naming convention

Path IDs use dot notation: `<source>.<flow>.<variant>`

Examples:
- `linkedin.easy_apply.standard`
- `xing.standard_apply.standard`
- `xing.standard_apply.salary_negotiation` (variant with extra salary step)
- `stepstone.quick_apply.standard`

Step tags extend the path ID: `<path_id>.step<N>.<name>`

Examples:
- `linkedin.easy_apply.standard.step1.contact`
- `linkedin.easy_apply.standard.step5.review`

## Path versioning

Each path has a version string (e.g., `v1`, `v2`). Versions are immutable —
once a path version is stored, it is never modified. Updates create a new version.

```
linkedin/easy_apply/standard_v1.json   # original recording
linkedin/easy_apply/standard_v2.json   # re-recorded after portal change
```

The latest canonical version is the default for replay. Older versions are kept
for audit and rollback.

## File format

All paths are stored as JSON, validated against `AriadnePath` Pydantic model.

```json
{
  "meta": {
    "source": "linkedin",
    "flow": "easy_apply",
    "version": "v1",
    "recorded_at": "2026-04-01T...",
    "recorded_by": "human",
    "status": "canonical",
    "total_steps": 5,
    "notes": "..."
  },
  "entry_point": { "..." },
  "path_id": "linkedin.easy_apply.standard",
  "steps": [ "..." ],
  "bifurcations": { "..." },
  "dead_ends": []
}
```

## Storage operations

### Write operations

| Operation | When | Input | Output |
|---|---|---|---|
| Store draft | Recording pipeline completes | AriadnePath (draft) | File in `data/ariadne/recordings/<session>/` |
| Promote to verified | Verification replay succeeds | Draft path reference | Status updated to `verified` |
| Promote to canonical | Operator approves | Verified path reference | Copied to packaged traces, status `canonical` |
| Store replay meta | After any replay | Replay result | File in job's ariadne node |

### Read operations

| Operation | When | Input | Output |
|---|---|---|---|
| Load canonical path | Motor needs to replay | source + flow (+ optional variant/version) | AriadnePath |
| Load draft/verified path | Review or verification | Session ID or path reference | AriadnePath |
| List paths for portal | Operator inspects available paths | source name | List of AriadnePath summaries |
| Load replay meta | Audit or debugging | source + job_id | Replay metadata |

### Path resolution

When a motor needs a path for a specific job, resolution follows this order:

1. Operator specifies exact path + version → use it
2. Operator specifies source + flow → find latest canonical version
3. No path specified → match portal's default flow → find latest canonical version
4. No canonical path exists → error (cannot replay without a path)

## Crawl4AI schema cache (temporary location)

The Crawl4AI extraction schema cache currently lives at
`data/ariadne/assets/crawl4ai_schemas/`. This is a temporary location —
target is a Crawl4AI motor-local `schemas/` folder.

Ariadne storage should NOT manage Crawl4AI schemas. They are motor-specific
assets, not Ariadne paths.

If a schema is source-controlled runtime configuration, keep it with the Crawl4AI
motor. If it is environment-generated cache data, keep it in runtime storage,
not in Ariadne's packaged path area.

## Open questions

1. Should packaged paths be plain JSON files or bundled into a single index file
   with embedded paths? Plain files are simpler to inspect; an index enables
   faster lookup.
2. Should recording session artifacts (raw timeline, screenshots) have a retention
   policy? They can grow large if many sessions are recorded.
3. Should Ariadne storage support path merging? (Two recordings of the same flow
   merged into one path with bifurcations for the differences.)
4. How does path resolution handle portals with multiple flows? (e.g., LinkedIn
   has Easy Apply and external ATS redirect — different flows, different paths.)
