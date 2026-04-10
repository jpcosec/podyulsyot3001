"""Render command."""

from __future__ import annotations

import argparse

from src.core.tools.render.main import main as render_main


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("render", help="Run document rendering only")
    p.add_argument("document", choices=["cv", "letter"])
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", dest="job_id")
    p.add_argument("--template")
    p.add_argument("--engine", default="tex", choices=["tex", "docx"])
    p.add_argument("--language", default="english")
    p.add_argument("--output")


def run(args: argparse.Namespace) -> int:
    argv = [
        args.document,
        "--source",
        args.source,
        "--engine",
        args.engine,
        "--language",
        args.language,
    ]
    if args.job_id:
        argv.extend(["--job-id", args.job_id])
    if args.template:
        argv.extend(["--template", args.template])
    if args.output:
        argv.extend(["--output", args.output])
    return render_main(argv)
