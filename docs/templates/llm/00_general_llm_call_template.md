# General LLM Call Template

## Purpose

Define one concrete and reusable template for LLM calls in `logic.py`.

This template is taxonomy-agnostic and intentionally explicit about inputs, outputs, prompts, and failures.

## Non-negotiable constraints

1. `logic.py` performs no file I/O.
2. `node.py` owns all artifact reads/writes.
3. LLM output must be schema-validated (Pydantic) before returning.
4. Prompt assets are node-local (`prompt/` folder).
5. No fallback-to-success on model or parse failures.

## Canonical runtime protocol

```python
from pydantic import BaseModel
from typing import Protocol


class ModelRequestError(RuntimeError):
    """Transport/API/runtime failure."""


class ModelSchemaError(RuntimeError):
    """Structured output missing or invalid."""


class LLMRuntime(Protocol):
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        model_ref: str,
        temperature: float,
    ) -> BaseModel: ...
```

## Reference implementation (Gemini)

This is the concrete baseline for the current stack:

```python
from google import genai
from google.genai import types
from pydantic import BaseModel


class GeminiRuntime:
    def __init__(self, client: genai.Client | None = None):
        self.client = client or genai.Client()

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        model_ref: str = "gemini-2.5-flash",
        temperature: float = 0.0,
    ) -> BaseModel:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=output_schema,
        )

        try:
            response = self.client.models.generate_content(
                model=model_ref,
                contents=user_prompt,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001
            raise ModelRequestError(f"gemini request failed: {exc}") from exc

        if response.parsed is None:
            raise ModelSchemaError("gemini returned no parsed structured output")

        return response.parsed
```

## Canonical `logic.py` skeleton

```python
from pydantic import BaseModel


class PromptBundle(BaseModel):
    system_prompt: str
    user_template: str
    prompt_ref: str
    prompt_version: str


class LogicInput(BaseModel):
    job_id: str
    payload: dict


class LogicOutput(BaseModel):
    schema_version: str
    doc_type: str
    data: dict


def run_logic(
    *,
    runtime: LLMRuntime,
    prompt_bundle: PromptBundle,
    logic_input: LogicInput,
    model_ref: str = "gemini-2.5-flash",
    temperature: float = 0.0,
) -> LogicOutput:
    user_prompt = prompt_bundle.user_template.format(
        job_id=logic_input.job_id,
        payload_json=logic_input.model_dump_json(indent=2),
    )

    output = runtime.generate_structured(
        system_prompt=prompt_bundle.system_prompt,
        user_prompt=user_prompt,
        output_schema=LogicOutput,
        model_ref=model_ref,
        temperature=temperature,
    )
    return LogicOutput.model_validate(output)
```

## Prompt management contract

Each LLM node folder should include:

```text
prompt/
  system.md
  user_template.md
  output_schema.json
  meta.yaml
  fewshots.jsonl        # optional
```

`meta.yaml` minimum fields:

```yaml
prompt_ref: match
prompt_version: "1.0"
owner: ai/nodes/match
```

## Input/output boundaries

`node.py` responsibilities:

- load and validate input artifacts,
- load prompt assets,
- call `run_logic(...)`,
- persist outputs,
- set routing state.

`logic.py` responsibilities:

- prepare prompt payload,
- call runtime,
- validate and return typed output.

## Failure routing contract

- `ModelRequestError` and `ModelSchemaError` are retryable model failures.
- Unknown exceptions are fail-stop unless explicitly classified.
- Never return empty/generic success objects on error.
