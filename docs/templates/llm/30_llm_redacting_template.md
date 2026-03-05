# LLM Redacting Template

## Category intent

`redacting`: draft narrative content for human review.

Primary output is dual:

- structured state JSON,
- narrative markdown draft.

## Entries (required)

- approved strategic context,
- approved upstream content dependencies,
- optional style/tone constraints.

Example entry contract:

```python
class RedactingInput(BaseModel):
    job_id: str
    context_ref: str
    approved_claims: list[dict]
    style_profile: dict = {}
```

## Outputs

- `nodes/<node>/proposed/state.json`
- `nodes/<node>/proposed/<content_file>.md` (for example `letter.md`, `to_render.md`, `application_email.md`)
- `nodes/<node>/proposed/view.md` (deterministic sync)
- `nodes/<node>/review/decision.md` (deterministic sync)

Review surfaces:

- always `generate_review_surface=True`.

## `logic.py` structure

```python
class RedactingState(BaseModel):
    schema_version: str
    doc_type: str
    content_ref: str
    consumed_claim_ids: list[str]
    metadata: dict


class RedactingOutput(BaseModel):
    state: RedactingState
    markdown: str
    filename: str


def run_logic(*, runtime: LLMRuntime, prompt_bundle: PromptBundle, logic_input: RedactingInput) -> RedactingOutput:
    ...
```

## Prompt management

- `prompt/system.md`: narrative constraints and anti-fabrication rules.
- `prompt/user_template.md`: explicit slots for claims/context/style.
- `prompt/output_schema.json`: state contract.
- `prompt/meta.yaml`: prompt identity/version.
- optional `fewshots.jsonl`: tone and structure examples.

Prompt rules:

1. narrative must consume only approved claims,
2. markdown style must match node target (motivation/CV/email),
3. output must include machine-readable consumption references.

## Node routing expectations

- returns `status: "pending_review"` on success,
- deterministic review parser node decides approve/regenerate/reject.

## Anti-wax checks

1. reject static template outputs that ignore job-specific context,
2. reject content with missing claim consumption refs,
3. reject success responses with empty markdown body.
