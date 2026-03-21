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

    @classmethod
    def from_env(cls) -> "LLMConfig":
        import os

        api_key = os.environ.get("LANGSMITH_API_KEY", "")
        return cls(
            langsmith_api_key=api_key or None,
            langsmith_enabled=bool(api_key),
            model=os.environ.get("PHD2_GEMINI_MODEL", "gemini-2.0-flash"),
        )
