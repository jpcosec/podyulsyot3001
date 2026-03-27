from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    model: str = "gemini-2.0-flash"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "phd-20"
    langsmith_endpoint: Optional[str] = None
    langsmith_enabled: bool = False
    langsmith_verification_required: bool = False

    @classmethod
    def from_env(cls) -> "LLMConfig":
        import os

        api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get(
            "LANGSMITH_KEY", ""
        )
        project = os.environ.get("LANGSMITH_PROJECT", "phd-20")
        endpoint = os.environ.get("LANGSMITH_ENDPOINT")
        model = (
            os.environ.get("PHD2_GEMINI_MODEL")
            or os.environ.get("GEMINI_MODEL")
            or "gemini-2.0-flash"
        )
        verification_required = os.environ.get(
            "PHD2_LANGSMITH_REQUIRE_VERIFICATION", ""
        ).lower() in {"1", "true", "yes", "on"}
        return cls(
            langsmith_api_key=api_key or None,
            langsmith_enabled=bool(api_key),
            langsmith_project=project,
            langsmith_endpoint=endpoint or None,
            langsmith_verification_required=verification_required,
            model=model,
        )

    def assert_verifiable(self) -> None:
        if self.langsmith_enabled:
            return
        raise RuntimeError(
            "LangSmith verification is required but LANGSMITH_API_KEY is missing"
        )
