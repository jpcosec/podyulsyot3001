"""Ariadne configuration - auto-loaded from .env."""

import os
from pathlib import Path
from functools import lru_cache

try:
    from dotenv import load_dotenv

    _DOTENV_LOADED = load_dotenv()
except ImportError:
    _DOTENV_LOADED = False


@lru_cache(maxsize=1)
def get_config(key: str, default: str = "") -> str:
    """Get config from environment, falling back to default."""
    return os.environ.get(key, default)


@lru_cache(maxsize=1)
def get_gemini_model() -> str:
    """Get Gemini model to use for LLM fallback.

    Defaults to gemini-3.1-flash (latest fast model).
    """
    model = get_config("GEMINI_MODEL", "gemini-3.1-flash")
    return model or "gemini-3.1-flash"


@lru_cache(maxsize=1)
def get_browseros_path() -> str | None:
    """Get BrowserOS appimage path."""
    return get_config("BROWSEROS_APPIMAGE_PATH", "")


@lru_cache(maxsize=1)
def get_google_api_key() -> str | None:
    """Get Google API key."""
    return get_config("GOOGLE_API_KEY", "")


def is_headless() -> bool:
    """Check if scraper should run headless."""
    return get_config("SCRAPER_HEADLESS", "true").lower() == "true"


# Auto-load on import
_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if _ENV_PATH.exists() and not _DOTENV_LOADED:
    load_dotenv(_ENV_PATH)
