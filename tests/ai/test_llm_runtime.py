"""Tests for structured LLM runtime behavior."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from src.ai.llm_runtime import LLMRuntime, LLMRuntimeResponseError


class _OutputSchema(BaseModel):
    value: str


class _FakeResponse:
    def __init__(self, text: str | None):
        self.text = text


class _FakeModel:
    def __init__(self, response_text: str | None):
        self.response_text = response_text
        self.calls: list[dict] = []

    def generate_content(self, user_prompt, **kwargs):
        self.calls.append({"user_prompt": user_prompt, **kwargs})
        return _FakeResponse(self.response_text)


def test_generate_structured_validates_schema_and_returns_model() -> None:
    model = _FakeModel('{"value": "ok"}')
    runtime = LLMRuntime(model=model)

    out = runtime.generate_structured(
        system_prompt="sys",
        user_prompt="user",
        output_schema=_OutputSchema,
    )

    assert out.value == "ok"
    assert len(model.calls) == 1
    call = model.calls[0]
    assert call["user_prompt"] == "user"
    assert call["system_instruction"] == "sys"
    assert call["generation_config"]["response_mime_type"] == "application/json"
    assert call["generation_config"]["response_schema"] is _OutputSchema


def test_generate_structured_fails_when_response_text_missing() -> None:
    runtime = LLMRuntime(model=_FakeModel(None))

    with pytest.raises(LLMRuntimeResponseError, match="no JSON text"):
        runtime.generate_structured(
            system_prompt="sys",
            user_prompt="user",
            output_schema=_OutputSchema,
        )


def test_generate_structured_fails_on_schema_mismatch() -> None:
    runtime = LLMRuntime(model=_FakeModel('{"unexpected": 1}'))

    with pytest.raises(LLMRuntimeResponseError, match="schema validation"):
        runtime.generate_structured(
            system_prompt="sys",
            user_prompt="user",
            output_schema=_OutputSchema,
        )


def test_generate_structured_uses_legacy_fallback_for_system_instruction_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _TypeErrorModel:
        def generate_content(self, *_args, **_kwargs):
            raise TypeError("unexpected keyword argument 'system_instruction'")

    runtime = LLMRuntime(model=_TypeErrorModel())

    def fake_legacy(*, system_prompt: str, user_prompt: str, generation_config: dict):
        assert system_prompt == "sys"
        assert user_prompt == "user"
        assert generation_config["response_mime_type"] == "application/json"
        return _FakeResponse('{"value": "fallback"}')

    monkeypatch.setattr(
        runtime, "_generate_with_legacy_system_instruction", fake_legacy
    )

    out = runtime.generate_structured(
        system_prompt="sys",
        user_prompt="user",
        output_schema=_OutputSchema,
    )

    assert out.value == "fallback"
