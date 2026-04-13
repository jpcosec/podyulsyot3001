# Context Pills

Context pills are short, disposable summaries that give zero-context agents exactly what they need to avoid architecture violations. They are **derived from source** — always secondary to the code they describe. When source changes, delete and recreate; never patch in place.

**Hard limit: 50 lines per pill.** If a pill needs more, it is doing too much — split it.

---

## Frontmatter (required on every pill)

```yaml
---
type: guardrail | decision | pattern | model
domain: ariadne | cli | scraping | architecture   # layer this pill belongs to
source: path/to/file.py:line                      # authoritative source of truth
law: 1-4                                           # guardrails only, when applicable
---
```

---

## Tree index

Pills are indexed by `domain > type`. Use this to find relevant pills when preparing an issue.

```
architecture
  ├─ decision
  │    └─ ariadne-langgraph.md
  ├─ guardrail
  │    └─ dip-enforcement.md
  └─ pattern
       ├─ async-test-pattern.md
       ├─ log-tags.md
       ├─ mock-executor-pattern.md
       ├─ registry-pattern.md
       ├─ structured-output-pattern.md
       └─ test-spy-pattern.md

ariadne
  ├─ decision
  │    └─ gemini-flash-default.md
  ├─ guardrail
  │    ├─ law-1-async.md
  │    ├─ law-3-dom-hostility.md
  │    └─ law-4-finite-routing.md
  ├─ model
  │    ├─ ariadne-map-model.md
  │    ├─ ariadne-models.md
  │    ├─ error-contract.md
  │    └─ fitness-map-model.md
  └─ pattern
       ├─ exception-pattern.md
       ├─ node-pattern.md
       └─ som-pattern.md

       └─ som-pattern.md

cli
  ├─ guardrail
  │    └─ law-2-single-browser.md
  └─ pattern
       └─ cli-universal-pattern.md

scraping
  ├─ decision
  │    └─ browseros-mcp-contract.md
  └─ pattern
       ├─ promotion-pattern.md
       ├─ recording-pattern.md
       └─ smoke-test-pattern.md
```

When creating a new pill, place it in the correct branch of this tree and add it here.

---

## Types and required sections

### `guardrail`
Non-negotiable constraint backed by a fitness test. Routed to issues that could violate it.
Required sections: `## Rule` · `## ❌ Forbidden` · `## ✅ Correct` · `## Verify`

### `decision`
Architectural choice with rationale. Routed to issues that touch the layer where the decision was made.
Required sections: `## Decision` · `## Rationale` · `## Trade-offs` · `## Do not reverse unless`

### `pattern`
Positive recipe for implementing something correctly. Routed to implementation issues in its domain.
Required sections: `## Pattern` · `## Implementation` · `## When to use` · `## Verify`

### `model`
Data shape reference. Routed to issues that read or write the described structure.
Required sections: `## Structure` · `## Usage` · `## Verify`

---

## Staleness rules by type

| Type | Stale when |
|---|---|
| `guardrail` | `source` file renamed/deleted; threshold in pill differs from code; `## Verify` command no longer exists |
| `decision` | Dependency removed from codebase; ADR explicitly reverses the decision |
| `pattern` | Function signature, config key, or import path in pill differs from `source` |
| `model` | Any field in `## Structure` added, renamed, or removed in `source` |
