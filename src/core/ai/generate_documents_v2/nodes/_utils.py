"""Internal utilities shared across generate_documents_v2 nodes."""

import os


def _google_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
