# Feedback Memory System

Related references:

- `docs/architecture/artifact_schemas.md`
- `docs/architecture/claim_admissibility_and_policy.md`
- `docs/architecture/graph_definition.md`

## Purpose

Feedback is a transversal capability of the system, not a one-off exception attached only to matching. Every reviewable stage can produce feedback that improves the current case immediately and persists as reusable knowledge for future applications.

---

## Design principles

Each feedback item must support:

1. **Local correction**: applies to the current case immediately.
2. **Historical reuse**: can be reused in future applications when relevant.
3. **Stage awareness**: the system knows which stage(s) the feedback affects.
4. **Type awareness**: the system knows whether the feedback is factual, strategic, stylistic, etc.
5. **Controlled reuse**: feedback is retrieved selectively, not dumped wholesale into every prompt.

---

## Classification dimensions

### 1. Scope

- `local`: only useful for one application.
- `global`: reusable in future applications.

### 2. Stage

- `extraction`
- `matching`
- `application_context`
- `motivation_letter`
- `cv_tailoring`
- `email`
- `render`

### 3. Type

- `factual`: truthfulness / claim verification.
- `strategic`: what to emphasize, what to downplay.
- `stylistic`: tone, register, phrasing.
- `structural`: order, sections, formatting, layout.
- `process`: workflow rules, review rules, regeneration rules.

### 4. Reusability

- `high`: broadly applicable across applications.
- `medium`: applicable in similar contexts.
- `low`: mostly case-specific.

### 5. Resolution

- `accepted`: incorporated into active memory.
- `partial`: partially applied.
- `rejected`: considered and declined.
- `pending`: awaiting resolution.

---

## Feedback event schema

Each feedback event is stored as a JSON file at `feedback/events/<stage>/<timestamp>.json`.

```json
{
  "schema_version": "1.0",
  "feedback_id": "fb_000001",
  "created_at": "2026-03-03T15:05:00Z",
  "scope": "global",
  "resolution": "accepted",
  "reusability": "high",
  "source": {
    "job_id": "201397",
    "url": "https://example.org/phd-position",
    "reviewer": "human",
    "stage_origin": "matching"
  },
  "target": {
    "primary_stage": "matching",
    "affects_stages": ["matching", "motivation_letter", "cv_tailoring"]
  },
  "classification": {
    "type": "strategic",
    "domain": ["phd", "academic", "germany"],
    "tags": ["research-fit", "tone", "emphasis"]
  },
  "content": {
    "comment": "Do not overemphasize industry delivery when the position is strongly academic.",
    "rationale": "The target audience is academic and will value research depth over production framing.",
    "normalized_rule": "For strongly academic applications, foreground research trajectory before industry execution."
  },
  "application": {
    "applies_to_current_case": true,
    "current_case_action": "revise_match_weights",
    "reusable_summary": "In academic applications, prioritize research trajectory and publication signal over delivery framing."
  },
  "evidence": {
    "triggered_by_text": ["industry-grade AI solutions", "enterprise deployment"],
    "linked_artifacts": [
      "nodes/match/proposed/view.md",
      "nodes/review_match/approved/state.json"
    ]
  },
  "quality": {
    "confidence": 0.92,
    "reviewed_against_history": true,
    "conflict_status": "none"
  }
}
```

---

## Storage model

The system uses a three-layer storage model:

### 1. Raw event log

- Path: `feedback/events/<stage>/<timestamp>.json`
- Append-only record of all feedback events.
- Useful for traceability and audits.
- Never edited after creation.

### 2. Active memory

- Path: `feedback/active_memory.yaml`
- Distilled reusable rules derived from accepted historical feedback.
- Compact enough to be injected into prompts.
- Updated by the `feedback_distill` process.

### 3. Conflict registry

- Path: `feedback/conflicts.yaml`
- Explicit conflicts or alternative rules requiring human resolution.
- See conflict model below.

---

## Active memory format

```yaml
matching:
  strategic:
    - rule: "For academic applications, prioritize research trajectory over delivery framing."
      tags: [phd, academic, research-fit]
      confidence: 0.92

motivation_letter:
  stylistic:
    - rule: "Avoid generic excitement claims; tie motivation to concrete research questions."
      tags: [phd, academic, writing]
      confidence: 0.95

cv_tailoring:
  factual:
    - rule: "Do not imply hands-on data collection experience unless explicitly verified."
      tags: [truthfulness, claims]
      confidence: 0.99

render:
  structural:
    - rule: "Default to concise academic formatting when the application expects formal materials."
      tags: [formatting, academic]
      confidence: 0.81
```

---

## Retrieval strategy

Do not inject the entire historical log into every stage. Instead, retrieve feedback using filters:

- target stage
- domain tags
- type
- reusability
- confidence threshold
- recency
- conflict status

### Per-stage retrieval policy

**Matching stage**:
- Retrieve `strategic` + `factual` feedback.
- Prioritize `phd` / `academic` / `research-fit` tags.
- Exclude low-confidence feedback.
- Include both global and current-case local items.

**Motivation letter stage**:
- Retrieve `factual` + `strategic` + `stylistic` feedback.
- Prioritize accepted, high-reusability rules.
- Include stage-specific writing constraints.

**CV tailoring stage**:
- Retrieve `factual` + `strategic` + `structural` feedback.
- Prioritize constraints related to claims, emphasis, brevity, and ordering.

**Email stage**:
- Retrieve `stylistic` + `strategic` feedback.
- Prioritize concise and audience-appropriate rules.

**Render stage**:
- Retrieve `structural` + `process` feedback.
- Prioritize page limit, formatting, and packaging rules.

---

## Conflict model

### Conflict classes

- `direct_contradiction`: two rules prescribe opposite actions.
- `scope_conflict`: local rule conflicts with global default.
- `priority_conflict`: competing rules for same target and stage.
- `temporal_conflict`: superseded guidance with unclear precedence.

### Conflict schema

```yaml
conflict_id: "conf_001"
rule_ids: ["fb_000012", "fb_000034"]
conflict_type: "direct_contradiction"
detected_at: "2026-03-04T10:00:00Z"
status: "open"
resolution_policy: "Pending human review"
```

Minimum fields:

- `conflict_id`
- `rule_ids`: the conflicting feedback ids.
- `conflict_type`
- `detected_at`
- `status`: `open` | `resolved` | `suppressed`.
- `resolution_policy`

### Resolution policy

- Unresolved conflicts are excluded from automatic prompt injection unless a deterministic precedence rule selects one unambiguously.
- Resolved conflicts are marked with the winning rule and rationale.
- Suppressed conflicts are acknowledged but intentionally deferred.

---

## Operational pattern per stage

Each reviewable stage follows this feedback lifecycle:

1. **Generate proposal**: node produces proposed artifacts.
2. **Receive review**: human reviews and provides decisions.
3. **Apply local feedback**: corrections applied to current case immediately.
4. **Persist as historical event**: review feedback stored as `feedback/events/<stage>/<timestamp>.json`.
5. **Distill into active memory**: reusable part merged into `feedback/active_memory.yaml` when appropriate.
6. **Continue to next stage**: pipeline resumes with enriched context.

Abstractly:

```
propose -> review -> local correction -> historical persistence -> reusable memory update -> next stage
```

---

## System framing

The pipeline is better understood as:

> "understand -> propose -> review -> learn -> generate -> review -> learn -> deliver"

rather than as a simple linear document-generation pipeline. Feedback memory is what makes this learning loop possible.
