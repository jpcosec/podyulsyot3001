# Fase 2 - Neo4j Knowledge Graph

## Goal

Introduce Neo4j only after the local JSON editor proves the right review model and data interactions.

## Why this is phase 2

- Neo4j solves scale, historization, and cross-job querying.
- It is not required to validate the first useful operator workflow.
- Moving too early would mix UI uncertainty with infrastructure migration risk.

## Trigger for starting this phase

Begin only when phase 1 has stabilized:

1. Core editor interactions are accepted.
2. The local JSON shape is clear.
3. The review workbench needs cross-job querying, history, or higher-volume persistence.

## Target capabilities

- Stable node and edge identities.
- Review historization across runs and jobs.
- Cross-job queries.
- Rich provenance links between source text, extracted nodes, matches, and generated content.

## Scope

- Migrate from local JSON-backed editing to graph-backed persistence.
- Preserve the UI concepts validated in phase 1.
- Avoid redesigning the interaction model during the database migration.

## Non-goals

- Do not use Neo4j as an excuse to restart the frontend from zero.
- Do not couple this phase to a mandatory full LangChain rewrite.

## Done definition

- The workbench can persist and query the validated review model in Neo4j.
- The migration preserves operator workflows already accepted in phase 1.
