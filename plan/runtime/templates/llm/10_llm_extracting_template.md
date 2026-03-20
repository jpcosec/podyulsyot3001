# LLM Extracting Template

## Category intent

`extracting`: distill or consolidate semantics into structured machine state.

Primary output is JSON state, not narrative markdown.

## Entries (required)

- one or more approved upstream states,
- optional profile snapshot,
- optional active feedback memory slice.

Example entry contract:

```python
class ExtractingInput(BaseModel):
    job_id: str
    upstream_refs: list[str]
    payload: dict
    constraints: dict = {}
```

## Outputs

- `nodes/<node>/proposed/state.json`
- optional `nodes/<node>/approved/state.json` if non-gated step is auto-promoted by deterministic rule.

Review surfaces:

- default is `generate_review_surface=False`.

## `logic.py` structure

```python
class ExtractingOutput(BaseModel):
    schema_version: str
    doc_type: str
    extracted_items: list[dict]
    summary: dict


def run_logic(*, runtime: LLMRuntime, prompt_bundle: PromptBundle, logic_input: ExtractingInput) -> ExtractingOutput:
    ...
```

## Prompt management

- `prompt/system.md`: extraction policy and anti-hallucination constraints.
- `prompt/user_template.md`: explicit source slots and extraction task framing.
- `prompt/output_schema.json`: strict schema reflecting `ExtractingOutput`.
- `prompt/meta.yaml`: prompt identity and version.

Prompt rules:

1. enforce evidence-grounded extraction,
2. forbid free narrative sections not represented in schema,
3. require deterministic field naming.

## Node routing expectations

- usually returns `status: "running"` (non-gated),
- retryable model failures set `error_state`.

## Anti-wax checks

1. output must validate schema with no missing required fields,
2. no placeholder values (`"TBD"`, `"Unknown"`) unless explicitly allowed by schema,
3. extraction claims must be source-grounded.
