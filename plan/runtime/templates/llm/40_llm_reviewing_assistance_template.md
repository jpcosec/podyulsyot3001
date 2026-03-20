# LLM Reviewing (Assistance) Template

## Category intent

`reviewing` in LLM taxonomy means assistance analysis over reviewed artifacts.

It is non-gating and has no approval authority.

## Entries (required)

- proposed state from upstream node,
- reviewed markdown and/or parsed decision payload,
- optional feedback memory context.

Example entry contract:

```python
class ReviewingAssistInput(BaseModel):
    job_id: str
    upstream_proposed_ref: str
    review_markdown: str
    review_decision_json: dict | None = None
```

## Outputs

- `nodes/<node>/proposed/state.json` (analysis, distilled lessons, or summaries)
- optional feedback event payloads routed to feedback memory flow.

No review surface generation by default.

## `logic.py` structure

```python
class ReviewingAssistOutput(BaseModel):
    schema_version: str
    doc_type: str
    insights: list[dict]
    reusable_rules: list[dict]


def run_logic(*, runtime: LLMRuntime, prompt_bundle: PromptBundle, logic_input: ReviewingAssistInput) -> ReviewingAssistOutput:
    ...
```

## Prompt management

- `prompt/system.md`: explicitly says assistance-only, no gate authority.
- `prompt/user_template.md`: includes reviewed content and extraction goals.
- `prompt/output_schema.json`: strict analysis schema.
- `prompt/meta.yaml`: prompt identity/version.

Prompt rules:

1. do not emit approve/reject decisions,
2. do not rewrite canonical approved artifacts,
3. produce concise, reusable analysis structures.

## Node routing expectations

- returns `status: "running"` on success,
- does not set `review_decision`.

## Anti-wax checks

1. assistance output must be tied to actual reviewed input,
2. avoid generic advice blocks detached from job context,
3. ensure deterministic review-gate parser remains single approval authority.
