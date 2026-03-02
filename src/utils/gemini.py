import importlib
import os
from pathlib import Path
from typing import Any

genai: Any | None = None
_USING_GENAI_CLIENT: bool | None = None


def _load_gemini_sdk() -> tuple[Any, bool]:
    try:
        return importlib.import_module("google.genai"), True
    except ImportError:
        try:
            return importlib.import_module("google.generativeai"), False
        except ImportError as exc:
            raise ImportError(
                "Gemini SDK not installed. Install `google-genai` or `google-generativeai`."
            ) from exc


class GeminiClient:
    """Shared Gemini client. Reads GOOGLE_API_KEY and GEMINI_MODEL from env."""

    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Set it in your shell or in .env at repo root."
            )

        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client: Any = None
        self._legacy_model: Any = None

        global genai, _USING_GENAI_CLIENT
        if genai is None:
            genai, _USING_GENAI_CLIENT = _load_gemini_sdk()
        if _USING_GENAI_CLIENT is None:
            _USING_GENAI_CLIENT = False
        if genai is None:
            raise ImportError(
                "Gemini SDK not installed. Install `google-genai` or `google-generativeai`."
            )

        if _USING_GENAI_CLIENT:
            self._client = genai.Client(api_key=api_key)
            return

        genai.configure(api_key=api_key)
        self._legacy_model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str) -> str:
        if _USING_GENAI_CLIENT:
            if self._client is None:
                raise ValueError("Gemini client is not initialized")
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text

        if self._legacy_model is None:
            raise ValueError("Gemini legacy model is not initialized")
        response = self._legacy_model.generate_content(prompt)
        if getattr(response, "text", None):
            return response.text
        raise ValueError("Gemini response did not contain text")

    @staticmethod
    def _load_env_defaults() -> None:
        repo_root = Path(__file__).resolve().parents[2]
        candidate_paths = [
            repo_root / ".env",
            Path.cwd() / ".env",
        ]

        explicit_path = os.getenv("PHD_DOTENV_PATH")
        if explicit_path:
            candidate_paths.insert(0, Path(explicit_path).expanduser())

        for path in candidate_paths:
            GeminiClient._apply_dotenv(path)

    @staticmethod
    def _apply_dotenv(path: Path) -> None:
        if not path.exists() or not path.is_file():
            return

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("export "):
                line = line[len("export ") :].strip()

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
