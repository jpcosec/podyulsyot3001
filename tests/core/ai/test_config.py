"""Tests for LLMConfig."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestLLMConfigDefaults:
    def test_default_model_is_gemini_2_0_flash(self):
        from src.core.ai.config import LLMConfig

        cfg = LLMConfig()
        assert cfg.model == "gemini-2.0-flash"

    def test_default_temperature_is_01(self):
        from src.core.ai.config import LLMConfig

        cfg = LLMConfig()
        assert cfg.temperature == 0.1

    def test_default_langsmith_disabled(self):
        from src.core.ai.config import LLMConfig

        cfg = LLMConfig()
        assert cfg.langsmith_enabled is False
        assert cfg.langsmith_api_key is None

    def test_default_langsmith_project_is_phd_20(self):
        from src.core.ai.config import LLMConfig

        cfg = LLMConfig()
        assert cfg.langsmith_project == "phd-20"


class TestLLMConfigFromEnv:
    def test_langsmith_enabled_when_key_set(self):
        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key-123"}):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.langsmith_enabled is True
            assert cfg.langsmith_api_key == "test-key-123"

    def test_langsmith_disabled_when_key_empty(self):
        with patch.dict(os.environ, {"LANGSMITH_API_KEY": ""}):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.langsmith_enabled is False
            assert cfg.langsmith_api_key is None

    def test_langsmith_disabled_when_key_not_set(self):
        env = os.environ.copy()
        env.pop("LANGSMITH_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.langsmith_enabled is False
            assert cfg.langsmith_api_key is None

    def test_langsmith_enabled_when_legacy_key_set(self):
        with patch.dict(os.environ, {"LANGSMITH_KEY": "legacy-key-123"}):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.langsmith_enabled is True
            assert cfg.langsmith_api_key == "legacy-key-123"

    def test_model_from_env(self):
        with patch.dict(os.environ, {"PHD2_GEMINI_MODEL": "gemini-2.5-pro"}):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.model == "gemini-2.5-pro"

    def test_model_defaults_to_gemini_2_0_flash(self):
        env = os.environ.copy()
        env.pop("PHD2_GEMINI_MODEL", None)
        with patch.dict(os.environ, env, clear=True):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.model == "gemini-2.0-flash"

    def test_project_and_endpoint_from_env(self):
        with patch.dict(
            os.environ,
            {
                "LANGSMITH_API_KEY": "k",
                "LANGSMITH_PROJECT": "phd-evals",
                "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com",
            },
        ):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            assert cfg.langsmith_project == "phd-evals"
            assert cfg.langsmith_endpoint == "https://api.smith.langchain.com"

    def test_assert_verifiable_raises_when_key_missing(self):
        env = os.environ.copy()
        env.pop("LANGSMITH_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            from src.core.ai.config import LLMConfig

            cfg = LLMConfig.from_env()
            with pytest.raises(RuntimeError, match="LANGSMITH_API_KEY"):
                cfg.assert_verifiable()
