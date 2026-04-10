"""CLI commands package."""

from __future__ import annotations

from src.cli.commands.api import run as run_api
from src.cli.commands.pipeline import run as run_pipeline
from src.cli.commands.batch import run as run_batch
from src.cli.commands.translate import run as run_translate
from src.cli.commands.match import run as run_match
from src.cli.commands.generate import run as run_generate
from src.cli.commands.render import run as run_render
from src.cli.commands.review import run as run_review
from src.cli.commands.demo import run as run_demo  # noqa: F401

COMMAND_HANDLERS = {
    "api": run_api,
    "pipeline": run_pipeline,
    "run-batch": run_batch,
    "translate": run_translate,
    "match": run_match,
    "generate": run_generate,
    "render": run_render,
    "review": run_review,
    "demo": run_demo,
}

__all__ = [
    "COMMAND_HANDLERS",
    "run_api",
    "run_pipeline",
    "run_batch",
    "run_translate",
    "run_match",
    "run_generate",
    "run_render",
    "run_review",
    "run_demo",
]
