# JSON-First Scraping Migration

## Goal

Keep scraping in one bounded subsystem under `src/core/scraping/` and make JSON artifacts the stable boundary for downstream workflow code.

## Core decision

The workflow node should no longer contain scraping behavior directly. It should call the scraping subsystem and receive normalized JSON outputs.

## Why JSON-first

- Scraping outputs remain partially source-dependent.
- JSON is the safest stable boundary between volatile extraction and downstream processing.
- A JSON-first trail improves auditability, provenance, recovery, and reprocessing.

## Target operating model

- one core scraping subsystem
- many source adapters behind a registry
- one canonical JSON output contract for the rest of the pipeline
- raw and normalized artifacts both preserved

## Logical layers

1. Source adapters.
2. Registry.
3. Fetch layer.
4. Extraction layer.
5. Normalization layer.
6. Artifact layer.

## Recommended output layers

- fetch metadata JSON
- listing crawl JSON
- source extraction JSON
- canonical scrape JSON

## Migration phases

1. Copy and bound the subsystem.
2. Define the PhD2 facade boundary.
3. Rewire the scrape node to the facade.
4. Expand source coverage only after the boundary is stable.

## Done definition

- Scraping behavior lives in `src/core/scraping/`.
- Node logic stays thin.
- JSON artifacts are the canonical handoff to downstream nodes.
