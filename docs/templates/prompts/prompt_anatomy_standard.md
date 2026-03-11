# Prompt Anatomy Standard (System + User Template)

Related references:

- `docs/templates/llm/00_general_llm_call_template.md`
- `docs/templates/prompts/README.md`
- `docs/reference/contract_composition_framework.md`

## Purpose

This document defines the canonical prompt structure for all LLM nodes in PhD 2.0.

Each node-local prompt folder should include exactly two primary prompt files:

1. `system.md` (static guardrails),
2. `user_template.md` (Jinja2-rendered runtime task).

This standard is used to reduce output variance and prevent prompt drift.

## File split contract

### `system.md`

Static policy and role definition.

Rules:

- no runtime variables,
- concise and constraint-focused,
- defines non-negotiable safety and output rules.

### `user_template.md`

Runtime task execution template.

Rules:

- rendered with Jinja2 from `logic_input.model_dump()`,
- separates instructions from input payload,
- may include conditional blocks for optional sections (for example feedback memory).

## Canonical structure for `system.md`

Use these three sections in this order:

```markdown
# 1. Role and Objective
You are the [taxonomy role] engine for PhD 2.0.
Your only objective is [clear task objective].

# 2. Hard Constraints
You must obey all rules below without exception:
- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

# 3. Output Contract
Return only a JSON object that matches the schema provided by the runtime.
Do not include explanations or markdown code fences.
```

Examples of hard constraints:

- do not invent facts not present in inputs,
- do not assume technologies not explicitly stated,
- keep required vs optional distinctions explicit.

## Canonical structure for `user_template.md`

Use these four blocks in this order:

```markdown
# 1. Task Context
The following [artifact type] is provided for Job ID: {{ job_id }}.

# 2. Input Data
<input_data>
{{ source_text_md }}
</input_data>

{% if active_feedback %}
# 3. Active Feedback Memory
Apply the following reusable review rules:
<feedback_rules>
{% for rule in active_feedback %}
- {{ rule.rule }} (confidence: {{ rule.confidence }})
{% endfor %}
</feedback_rules>
{% endif %}

# 4. Execution Steps
1. Read all content inside `<input_data>`.
2. Execute the required extraction/matching/redacting steps for this node.
3. Build output fields required by the schema.
4. Return only schema-compliant JSON.
```

## Why this structure is robust

1. XML-like tags (`<input_data>`) isolate data from instructions and reduce accidental instruction injection.
2. Jinja2 conditionals include optional sections only when needed, reducing token noise.
3. Explicit execution steps improve consistency of model behavior across runs.
4. Separation of static constraints (`system.md`) and dynamic payload (`user_template.md`) reduces maintenance risk.

## Implementation rule for node code

`logic.py` should render `user_template.md` through the shared prompt manager and pass both prompts to runtime:

```python
user_prompt = render_user_template(
    prompt_dir=Path("prompt"),
    template_name="user_template.md",
    payload=logic_input.model_dump(),
)

output = runtime.generate_structured(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    output_schema=ExpectedSchema,
)
```

Missing Jinja variables must fail fast (strict rendering).
