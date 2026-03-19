# JSON-First Scraping Subsystem Migration Plan

## Purpose

Define the logical migration from the current single-source scraping implementation to a multi-source scraping subsystem that lives entirely under `src/core/`, is heavily inspired by `postulator3000`, and produces JSON-first artifacts suitable for later ingestion into a large node database.

This document is intentionally about system logic and migration shape, not implementation details.

## Core Decision

The scraping machinery should be copied into one bounded subsystem under:

- `src/core/scraping/`

This subsystem becomes the single runtime surface for:

- source-specific scraping rules
- source discovery and registration
- listing crawling
- page fetching
- extraction heuristics
- source-specific page handling
- normalization into canonical JSON artifacts

The workflow node should no longer contain scraping behavior directly. It should only call this subsystem and receive normalized JSON outputs.

## Primary Design Goal

Prioritize JSON artifacts over tightly structured intermediate Python models.

Reasoning:

- The long-term system target includes a large node database.
- Scraping outputs will remain partially unstructured and source-dependent.
- JSON is the most stable boundary between volatile source-specific extraction and later graph/node ingestion.
- A JSON-first artifact trail improves auditability, recovery, provenance, and reprocessing.

## Strategic Approach

Do not redesign the subsystem from zero.

Instead:

1. Copy the existing `postulator3000` scraping machinery into `src/core/scraping/`.
2. Preserve the broad architectural separation already present there.
3. Trim and adapt it to this repository’s narrower pipeline needs.
4. Reframe the outputs around PhD2 canonical JSON artifacts.

This approach is preferred because it is easier to adapt a working modular scraping system than to incrementally extend the current minimal TU-Berlin-shaped logic.

## Current Problem

The current scraping logic is effectively single-source in behavior even where it looks generic.

The current limitations are:

- listing crawl assumptions are tied to a single URL pattern and pagination shape
- job id extraction is tied to a single path convention
- detail page extraction is generic HTML stripping rather than source-aware content extraction
- the `scrape` node contains operational scraping behavior directly
- source-specific particularities are not isolated behind adapters
- outputs are too thin for future graph-oriented provenance and recovery workflows

## Target Operating Model

The target model is:

- one core scraping subsystem
- many source adapters behind a registry
- one canonical JSON output contract for the rest of the pipeline
- source-specific extraction isolated from graph execution logic
- raw and normalized artifacts both preserved

## Logical Boundaries

### 1. Source Adapter Layer

Each supported source should have an adapter that declares:

- what domains it handles
- whether it supports listing crawl
- whether it supports detail-page scraping
- whether it requires browser rendering
- how identifiers are discovered
- what extraction strategy it uses

Each adapter is responsible for understanding the particularities of that source only.

### 2. Registry Layer

A registry should decide which adapter to use based on:

- explicit source key
- domain match
- page capability

This avoids spreading source resolution logic across the pipeline.

### 3. Fetch Layer

Fetching should be treated as a separate concern from extraction.

Possible fetch modes:

- plain HTTP fetch
- browser-rendered fetch
- fallback fetch path when the preferred mode fails

The selected fetch mode should be recorded in JSON metadata for auditability.

### 4. Extraction Layer

Extraction should convert fetched page content into source-aware JSON describing:

- detected page type
- extracted title
- extracted content/body text
- extracted sections when available
- extraction warnings
- extraction confidence or quality signals
- provenance hints such as selectors or strategy used

This layer should tolerate variation without forcing premature full normalization.

### 5. Normalization Layer

A normalization layer should convert source-specific extraction output into the canonical scrape JSON consumed by the rest of the pipeline.

This is the key boundary between:

- unstable source-specific scraping behavior
- stable downstream processing

### 6. Artifact Layer

The subsystem should persist a full JSON-centered artifact trail, including:

- fetch metadata JSON
- listing crawl JSON when relevant
- source extraction JSON
- canonical scrape JSON
- optional raw HTML or response snapshot references

The canonical scrape JSON should be the artifact downstream nodes rely on.

## JSON-First Artifact Philosophy

The subsystem should prefer preserving information over prematurely compressing it.

That means:

- source extraction output can remain somewhat noisy
- canonical scrape JSON should remain conservative and stable
- raw metadata should be retained even when not immediately consumed
- provenance and recovery references should be stored explicitly

This is important because future graph ingestion may need to reinterpret the scraped result differently without re-scraping the source.

## Recommended Output Layers

### Fetch Metadata JSON

Should capture facts such as:

- requested URL
- resolved URL
- source key
- fetch mode
- timestamp
- HTTP-like status metadata when available
- warnings and retries
- raw artifact references

### Listing Crawl JSON

Should capture:

- listing URL
- crawl start and stop metadata
- discovered URLs
- discovered identifiers
- known identifiers
- new identifiers
- pagination metadata
- crawl stop reason

### Source Extraction JSON

Should capture:

- source key
- page type
- extracted title
- extracted text body
- extracted sections
- extracted structured hints if available
- language guess
- extraction warnings
- provenance hints

### Canonical Scrape JSON

Should capture the stable scrape contract for downstream workflow use, such as:

- `source`
- `source_url`
- `job_id` when derivable
- `raw_text`
- `original_language`
- `metadata`
- references to lower-level scrape artifacts

This should remain intentionally flexible enough to support many sources and later node-db mapping.

## What To Copy From Postulator

The imported subsystem should keep the useful architectural concepts from `postulator3000`, especially:

- base scraper or adapter abstraction
- scraper registry
- fetch strategy separation
- page model and selector organization
- source-specific scraper modules
- middleware ideas such as caching, retrying, rate limiting, and diagnostics

The goal is not to mirror all of `postulator3000` behavior. The goal is to reuse its modular scraping architecture and reshape it for this pipeline.

## What To Exclude Or Deprioritize

The following should not drive the first migration:

- broad job-board search product behavior
- highly specialized salary/company/location extraction features
- recorder/generator tooling
- large-scale selector generation workflows
- platform breadth beyond what is needed for current sources

Those are useful in a job-aggregation system, but not necessary to establish a stable scraping boundary for this repo.

## Migration Shape

### Phase 1. Copy And Bound The Subsystem

Copy the relevant `postulator3000` scraping machinery into:

- `src/core/scraping/`

Preserve recognizable structure so the imported system remains understandable and adaptable.

The result of this phase is not full integration. The result is a bounded subsystem in the correct location.

### Phase 2. Define The PhD2 Boundary

Define one PhD2-facing entry surface for the subsystem that supports:

- scrape one detail page
- crawl one listing source
- normalize outputs into PhD2 JSON artifacts

This should become the only supported access path from workflow nodes.

### Phase 3. Recast Outputs Around JSON Artifacts

Ensure the subsystem produces the four output layers:

- fetch metadata JSON
- listing crawl JSON
- source extraction JSON
- canonical scrape JSON

At this stage, the important change is not adding sources. It is stabilizing the artifact model.

### Phase 4. Port Existing TU Berlin Behavior Into An Explicit Adapter

Take the current TU Berlin assumptions and make them an explicit source adapter inside the new subsystem.

This matters because:

- it removes hidden source-coupling from generic helpers
- it validates the adapter model against the currently working source
- it provides the baseline regression target

### Phase 5. Add A Second Explicit Source Adapter

Add one more source with clearly different page characteristics.

This phase proves:

- the subsystem is genuinely multi-source
- the canonical JSON boundary is sufficient
- source-specific logic remains isolated

### Phase 6. Introduce Generic Detail-Page Fallback

Provide a fallback adapter for pages that are:

- directly fetchable
- server-rendered enough to extract readable text
- not yet worth a dedicated source adapter

This fallback should be treated as lower-confidence extraction, but still produce the same artifact layers.

### Phase 7. Rewire The Current `scrape` Node

Change the workflow `scrape` node so it:

- resolves source or domain
- delegates to the new `src/core/scraping/` subsystem
- persists artifact references
- places only canonical scrape JSON into graph state

From this point onward, node logic should no longer contain source-aware scraping rules.

### Phase 8. Expand Tests Around Artifact Contracts

Test the subsystem by validating:

- source adapter selection
- listing crawl results per source
- extraction quality on fixture pages
- canonical JSON contract stability
- fallback behavior
- raw/provenance artifact generation

The most important tests are contract and artifact tests, not just helper-function tests.

## Responsibilities Split

### Scraping Subsystem Responsibilities

- fetching
- crawling
- source-specific extraction
- source-specific page rules
- normalization
- artifact generation
- provenance capture

### Workflow Node Responsibilities

- providing source context and URLs
- invoking the scraping subsystem
- carrying canonical scrape JSON forward
- remaining ignorant of source-specific scraping details

## Why JSON Should Win Over Early Strong Structuring

The future node database should not force the scraper to overcommit to one narrow intermediate schema.

JSON-first artifacts are preferred because they:

- preserve source variability
- allow re-interpretation later
- support backfills and migrations
- improve observability and debugging
- make provenance easier to retain

The graph or node database should be built from these stable artifacts, rather than making the scraper itself responsible for final graph-ready semantics.

## Risks

### Risk 1. Over-importing Postulator Complexity

Copying too much machinery without narrowing the scope could create unnecessary maintenance cost.

Mitigation:

- import the architecture, not the entire product ambition
- trim aggressively after the copy boundary is established

### Risk 2. Canonical JSON Becoming Too Thin

If canonical outputs are too minimal, downstream graph ingestion may later require re-scraping.

Mitigation:

- preserve rich source extraction JSON and raw references alongside the canonical artifact

### Risk 3. Source Logic Leaking Back Into Nodes

If the graph node continues to special-case sources, the subsystem boundary will fail.

Mitigation:

- enforce a strict boundary where nodes only call the scraping service

### Risk 4. Generic Fallback Becoming The Default Crutch

If the fallback is overused, extraction quality will degrade across important sources.

Mitigation:

- treat fallback as acceptable for opportunistic ingestion, not as the long-term answer for core sources

## Acceptance Criteria

The migration should be considered successful when:

- all scraping machinery lives under `src/core/scraping/`
- the workflow node is thin and source-agnostic
- TU Berlin is represented by an explicit adapter, not hidden assumptions
- at least one additional source is supported through the same subsystem
- scraping outputs are persisted as JSON-first artifact sets
- downstream workflow reads only canonical scrape JSON
- raw and provenance-friendly artifacts remain available for future node-db ingestion

## End State

The desired end state is a bounded, JSON-first, multi-source scraping subsystem under `src/core/scraping/` that:

- is structurally inspired by `postulator3000`
- isolates per-source particularities cleanly
- preserves rich artifacts for later graph ingestion
- keeps workflow code simple
- scales by adding source adapters rather than rewriting pipeline nodes
