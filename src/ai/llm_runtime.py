"""Structured Gemini runtime wrapper for AI nodes."""

from __future__ import annotations

from typing import Any, TypeVar, cast

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMRuntimeDependencyError(RuntimeError):
    """Raised when Gemini SDK is not available."""


class LLMRuntimeResponseError(RuntimeError):
    """Raised when runtime response cannot be validated."""


class LLMRuntime:
    """Execute structured generation requests against Gemini."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        *,
        model: Any | None = None,
        safety_settings: Any | None = None,
    ):
        self.model_name = model_name
        self.safety_settings = safety_settings
        self.model = model or self._create_model(model_name)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[T],
    ) -> T:
        """Generate and validate a structured response."""
        generation_config = {
            "response_mime_type": "application/json",
            "response_schema": output_schema,
        }

        try:
            response = self.model.generate_content(
                user_prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings,
                system_instruction=system_prompt,
            )
        except TypeError as exc:
            if "system_instruction" not in str(exc):
                raise LLMRuntimeResponseError("gemini request failed") from exc
            response = self._generate_with_legacy_system_instruction(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                generation_config=generation_config,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMRuntimeResponseError("gemini request failed") from exc

        response_text = getattr(response, "text", None)
        if not isinstance(response_text, str) or not response_text.strip():
            raise LLMRuntimeResponseError("gemini response contained no JSON text")

        try:
            return output_schema.model_validate_json(response_text)
        except Exception as exc:  # noqa: BLE001
            raise LLMRuntimeResponseError(
                "gemini response failed schema validation"
            ) from exc

    def _create_model(self, model_name: str) -> Any:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMRuntimeDependencyError(
                "google-generativeai is required for LLMRuntime"
            ) from exc

        model_cls = getattr(genai, "GenerativeModel")
        return model_cls(model_name)

    def _generate_with_legacy_system_instruction(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        generation_config: dict[str, Any],
    ) -> Any:
        """Fallback path for google-generativeai versions without per-call system arg."""
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMRuntimeDependencyError(
                "google-generativeai is required for LLMRuntime"
            ) from exc

        model_cls = getattr(genai, "GenerativeModel")
        model = model_cls(self.model_name, system_instruction=system_prompt)
        try:
            return model.generate_content(
                user_prompt,
                generation_config=cast(Any, generation_config),
                safety_settings=self.safety_settings,
            )
        except Exception as exc:  # noqa: BLE001
            if not _supports_response_schema_error(exc):
                raise LLMRuntimeResponseError("gemini request failed") from exc

        fallback_config = {
            "response_mime_type": generation_config.get(
                "response_mime_type", "application/json"
            )
        }
        try:
            return model.generate_content(
                user_prompt,
                generation_config=cast(Any, fallback_config),
                safety_settings=self.safety_settings,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMRuntimeResponseError("gemini request failed") from exc


def _supports_response_schema_error(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = (
        "unknown field for schema",
        "response_schema",
        "schema has no",
    )
    return any(marker in message for marker in markers)
