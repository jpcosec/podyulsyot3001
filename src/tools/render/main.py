"""Unified CLI for document rendering."""

from __future__ import annotations

import argparse
import sys

from src.tools.render.coordinator import RenderCoordinator
from src.tools.render.request import RenderRequest
from src.tools.render.shared.metadata import parse_extra_vars


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universal document rendering pipeline"
    )
    parser.add_argument("document", nargs="?", choices=["cv", "letter"])
    parser.add_argument("--action", dest="legacy_action", choices=["cv", "letter"])
    parser.add_argument(
        "--source",
        required=True,
        help="Path to a source file or legacy job source name",
    )
    parser.add_argument(
        "--job-id", help="Legacy job identifier for job-bound rendering"
    )
    parser.add_argument("--template", help="Template/style name to use")
    parser.add_argument(
        "--engine", "--motor", dest="engine", default="tex", choices=["tex", "docx"]
    )
    parser.add_argument("--lang", "--language", dest="language", default="english")
    parser.add_argument("--output", help="Optional explicit output path")
    parser.add_argument(
        "--extra-vars", action="append", default=[], help="Extra KEY=VALUE metadata"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv or sys.argv[1:])
    document = args.document or args.legacy_action
    if document is None:
        parser.error("Document type is required. Use 'cv', 'letter', or --action.")

    try:
        extra_vars = parse_extra_vars(args.extra_vars)
        request = RenderRequest(
            document_type=document,
            engine=args.engine,
            style=args.template,
            language=args.language,
            source=args.source,
            source_kind="job" if args.job_id else "direct",
            job_id=args.job_id,
            output_path=args.output,
            extra_vars=extra_vars,
        )
        result = RenderCoordinator().render(request)
        print(result)
    except ValueError as exc:
        parser.error(str(exc))
        return 1
    except FileNotFoundError as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[Fatal Error] Render failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    main()
