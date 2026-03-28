"""Registry helpers for typed language bundles."""

from __future__ import annotations

from src.render.languages.de import LANGUAGE as DE_LANGUAGE
from src.render.languages.en import LANGUAGE as EN_LANGUAGE
from src.render.languages.es import LANGUAGE as ES_LANGUAGE
from src.render.languages.models import LanguageBundle

_LANGUAGES = {
    "en": EN_LANGUAGE,
    "es": ES_LANGUAGE,
    "de": DE_LANGUAGE,
}


def get_language_bundle(code: str) -> LanguageBundle:
    """Return the typed bundle for a language code."""
    try:
        payload = _LANGUAGES[code]
    except KeyError as exc:
        raise ValueError(f"Unsupported language '{code}'") from exc
    return LanguageBundle.model_validate(payload)
