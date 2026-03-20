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

Schema drift is primarily a load-time risk, not an edit-save risk. Manual saves help isolate local edits, but they do not protect against a representation schema that no longer matches incoming Neo4j data.

## Needed Contracts

- datasource registry
- schema registry
- reference identity scheme
- sync direction rules
  - import only
  - export only
  - bidirectional
- schema health check contract
  - validate declared attributes against a sample query/load payload
  - warn visibly on missing or mismatched attributes
  - never fail silently

## Initial De-Risking Rule

- start with a hardcoded schema in code
- extract to external YAML/JSON only after the load/validation path is stable

## What Breaks If Edited

- API client contracts
- persistence assumptions in graph editors
- future document explorer and schema explorer

## Acceptance

- every node/reference type can state where its source of truth lives
- UI can persist without hard-binding all logic to Neo4j
- loading a schema runs a health check and reports drift explicitly
