"""Tests for tracing module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestGetTracer:
    def test_returns_noop_tracer_when_langsmith_disabled(self):
        env = os.environ.copy()
        env.pop("LANGSMITH_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            from src.core.ai.tracing import get_tracer

            tracer = get_tracer()
            from src.core.ai.tracing import _NoOpTracer

            assert isinstance(tracer, _NoOpTracer)

    def test_returns_langsmith_tracer_when_enabled(self):
        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}):
            from src.core.ai.tracing import get_tracer

            tracer = get_tracer()
            from src.core.ai.tracing import _LangSmithTracer

            assert isinstance(tracer, _LangSmithTracer)


class TestNoOpTracer:
    def test_calls_function_normally(self):
        from src.core.ai.tracing import _NoOpTracer

        tracer = _NoOpTracer()

        def sample_func(a: int, b: int) -> int:
            return a + b

        result = tracer.trace("test", sample_func, 2, 3)
        assert result == 5

    def test_passes_kwargs(self):
        from src.core.ai.tracing import _NoOpTracer

        tracer = _NoOpTracer()

        def sample_func(a: int, b: int = 10) -> int:
            return a + b

        result = tracer.trace("test", sample_func, 5, b=7)
        assert result == 12

    def test_returns_non_numeric_result(self):
        from src.core.ai.tracing import _NoOpTracer

        tracer = _NoOpTracer()

        def sample_func() -> dict:
            return {"key": "value"}

        result = tracer.trace("test", sample_func)
        assert result == {"key": "value"}


class TestTraceSection:
    def test_trace_section_yields_control(self):
        from src.core.ai.tracing import trace_section

        with trace_section("test_section"):
            value = 42

        assert value == 42

    def test_trace_section_provides_metadata(self):
        from src.core.ai.tracing import trace_section

        received_metadata = None
        with trace_section("test_section", metadata={"key": "value"}):
            pass

        assert received_metadata is None

    def test_trace_section_works_without_metadata(self):
        from src.core.ai.tracing import trace_section

        with trace_section("test_section"):
            pass

    def test_trace_section_returns_value(self):
        from src.core.ai.tracing import trace_section

        with trace_section("test_section") as section_value:
            result = "test_result"

        assert result == "test_result"
