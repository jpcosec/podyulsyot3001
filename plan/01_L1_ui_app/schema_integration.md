# 04 External Data And Schema Integration

## Goal

Define how the UI graph connects to APIs, documents, schemas, databases, and graph stores without coupling the editor to one backend shape.

## Status

Partial in docs, weak in UI.

## Depends On

- `00_status_matrix.md`
- `01_graph_foundations.md`
- `01c_editor_state_and_history_contract.md`

## Enables

- `04a_document_explorer.md`
- backend-safe implementation sequencing

## Required Separation

- `workspace graph`
  - what the operator manipulates in the UI
- `domain graph`
  - canonical persisted business entities
- `artifact/document store`
  - markdown, text, screenshots, json, yaml, tables
- `graph projection`
  - optional Neo4j or other graph-db projection

## Recommendation

Neo4j should be treated as a projection/integration target, not the only source of UI truth.

## Needed Contracts

- datasource registry
- schema registry
- reference identity scheme
- sync direction rules
  - import only
  - export only
  - bidirectional

## What Breaks If Edited

- API client contracts
- persistence assumptions in graph editors
- future document explorer and schema explorer

## Acceptance

- every node/reference type can state where its source of truth lives
- UI can persist without hard-binding all logic to Neo4j
