"""Shared logging configuration for all pipeline entry points.

Loads ``config/logging.json`` via :func:`logging.config.dictConfig` so that
all loggers — including third-party ones (LangChain, LangGraph, httpx) — flow
into a single configured root logger.  Third-party loggers are capped at
``WARNING`` in the config file; application loggers (``src.*``) run at
``INFO`` and propagate naturally.

Usage (call once at entry-point startup, before any library code runs)::

    from src.shared.logging_config import configure_logging

    configure_logging()                              # console only
    configure_logging(log_file="translator_run.log")    # console + file
"""

from __future__ import annotations

import json
import logging
import logging.config
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "logging.json"


def configure_logging(log_file: str | None = None) -> None:
    """Configure root logger from ``config/logging.json``.

    Args:
        log_file: Optional filename (not full path) for a run-specific log
                  file.  Placed under the ``LOG_DIR`` env var (default:
                  ``logs/``).  Pass ``None`` for console-only output.
    """
    with _CONFIG_PATH.open(encoding="utf-8") as fh:
        config = json.load(fh)

    if log_file is not None:
        log_dir = Path(os.getenv("LOG_DIR", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": str(log_dir / log_file),
            "encoding": "utf-8",
        }
        config["root"]["handlers"] = ["console", "file"]

    logging.config.dictConfig(config)
