Historical Feedback Memory — Proposed Schema
============================================

Goal
----

All stages of the application pipeline are feedbackable.
Therefore, feedback should be treated as a transversal capability of the system,
not as a one-off exception attached only to matching.

Design principles
-----------------

Each feedback item should support:

1. Local correction
   - Applies to the current case immediately.

2. Historical reuse
   - Can be reused in future applications when relevant.

3. Stage awareness
   - The system must know which stage(s) the feedback affects.

4. Type awareness
   - The system must know whether the feedback is factual, strategic, stylistic, etc.

5. Controlled reuse
   - Feedback should be retrieved selectively, not dumped wholesale into every prompt.

Recommended schema
------------------

```yaml
feedback_id: fb_000001
created_at: "2026-03-03T12:00:00Z"

scope: global           # global | local
resolution: accepted    # accepted | rejected | partial | pending
reusability: high       # high | medium | low

source:
  job_id: phd_berlin_001
  url: "https://example.org/phd-position"
  reviewer: human
  stage_origin: matching

target:
  primary_stage: matching
  affects_stages:
    - matching
    - motivation_letter
    - cv_tailoring

classification:
  type: strategic       # factual | strategic | stylistic | structural | process
  domain:
    - phd
    - academic
    - germany
  tags:
    - research-fit
    - tone
    - emphasis

content:
  comment: >
    Do not overemphasize industry delivery when the position is strongly academic.
    Prioritize research agenda, publications, and cognitive-model motivation.
  rationale: >
    The target audience is academic and will value research depth over production framing.
  normalized_rule: >
    For strongly academic applications, foreground research trajectory before industry execution.

application:
  applies_to_current_case: true
  current_case_action: revise_match_weights
  reusable_summary: >
    In academic applications, prioritize research trajectory and publication signal over delivery framing.

evidence:
  triggered_by_text:
    - "industry-grade AI solutions"
    - "enterprise deployment"
  linked_artifacts:
    - planning/match_proposal.md
    - planning/reviewed_mapping.json

quality:
  confidence: 0.92
  reviewed_against_history: true
  conflict_status: none     # none | possible_conflict | conflict
```

Recommended classification dimensions
-------------------------------------

1. Scope
   - local: only useful for one application
   - global: reusable in future applications

2. Stage
   - extraction
   - matching
   - application_context
   - motivation_letter
   - cv_tailoring
   - email
   - render

3. Type
   - factual
     - truthfulness / claim verification
   - strategic
     - what to emphasize, what to downplay
   - stylistic
     - tone, register, phrasing
   - structural
     - order, sections, formatting, layout
   - process
     - workflow rules, review rules, regeneration rules

4. Reusability
   - high
   - medium
   - low

5. Resolution
   - accepted
   - partial
   - rejected
   - pending

Recommended retrieval strategy
------------------------------

Do not inject the entire historical log into every stage.

Instead, retrieve feedback using filters such as:
- target stage
- domain (phd, industry, academic, Germany, etc.)
- type
- tags
- reusability
- confidence
- recency
- conflict status

Example retrieval policy
------------------------

matching stage:
- retrieve strategic + factual feedback
- prioritize phd / academic / research-fit tags
- exclude low-confidence feedback
- include both global and current-case local items

motivation_letter stage:
- retrieve factual + strategic + stylistic feedback
- prioritize accepted, high-reusability rules
- include stage-specific writing constraints

cv_tailoring stage:
- retrieve factual + strategic + structural feedback
- prioritize constraints related to claims, emphasis, brevity, and ordering

email stage:
- retrieve stylistic + strategic feedback
- prioritize concise and audience-appropriate rules

render stage:
- retrieve structural + process feedback
- prioritize page limit, formatting, and packaging rules

Recommended storage model
-------------------------

Use at least two layers:

1. Raw historical log
   - append-only record of feedback events
   - useful for traceability and audits

2. Active memory
   - distilled reusable rules derived from accepted historical feedback
   - compact enough to be injected into prompts

Suggested file split
--------------------

1. feedback_events.jsonl
   - full granular historical log

2. feedback_memory_active.yaml
   - distilled active memory for prompt injection

3. feedback_conflicts.yaml
   - explicit conflicts or alternative rules requiring human choice

Suggested active-memory format
------------------------------

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

Operational pattern per stage
-----------------------------

Each stage should follow a common pattern:

1. Generate proposal
2. Receive review
3. Apply local feedback to current artifact
4. Persist review as historical event
5. Distill reusable part into active memory when appropriate
6. Continue to next stage

Abstractly:

proposal
-> review
-> local correction
-> historical persistence
-> reusable memory update
-> next stage

Final design takeaway
---------------------

The system is better understood as:

"understand -> propose -> review -> learn -> generate -> review -> learn -> deliver"

rather than as a simple linear document-generation pipeline.
