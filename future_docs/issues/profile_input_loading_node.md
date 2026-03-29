# Profile Input Loading Node

**Why deferred:** The pipeline currently works with profile evidence injected during `extract_bridge`, but the ownership and contract are still blurry.
**Last reviewed:** 2026-03-29

## Problem

The pipeline does not have a dedicated node responsible for loading and normalizing the profile input.

Today that concern is split across top-level graph glue in `src/graph/__init__.py`:

- environment/default path loading
- optional `profile_evidence_ref` loading
- legacy payload normalization
- persistence into `pipeline_inputs/profile_evidence.json`

That creates two issues:

1. the behavior is partially legacy-driven and easy to hardcode incorrectly
2. profile loading is hidden inside bridge/orchestration code instead of being an explicit pipeline step

## Why It Matters

- input contracts are harder to reason about
- legacy shape support can drift between code paths
- testing is harder because loading and normalization are not isolated
- the graph topology hides a real data-loading concern

## Current Smell

The current implementation suggests leftover legacy compatibility:

- list-shaped payloads are accepted
- dict payloads with `evidence` are also accepted
- normalization is not guaranteed to happen uniformly on every input path

This dual behavior is a signal that the profile contract is not fully consolidated yet.

## Recommended Change

Introduce a dedicated pipeline node for profile loading, for example:

- `load_profile`

Suggested responsibility:

- resolve profile source (`profile_evidence_ref`, env var, or default path)
- normalize the payload into the canonical shape
- persist the normalized artifact
- expose only the normalized ref/state needed by downstream nodes

Possible flow:

```text
scrape
  -> translate
  -> extract_bridge
  -> load_profile
  -> match_skill
```

Or, if requirements extraction and profile loading should be grouped differently:

```text
translate
  -> extract_requirements
  -> load_profile
  -> match_skill
```

## Suggested Steps

1. define the canonical profile evidence payload shape
2. isolate legacy compatibility in one loader/normalizer boundary
3. add a dedicated graph node for profile loading
4. make downstream nodes consume only normalized data or refs
5. add tests for all accepted input sources and legacy payload variants
