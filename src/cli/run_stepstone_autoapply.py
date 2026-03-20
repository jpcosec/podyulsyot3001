from __future__ import annotations

import argparse
import json

from src.core.application.stepstone_autoapply import (
    StepStoneAutoApplyRequest,
    run_stepstone_autoapply,
)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    request = StepStoneAutoApplyRequest(
        job_id=args.job_id,
        source_url=args.source_url,
        dry_run=not args.apply,
        timeout_seconds=args.timeout,
    )
    result = run_stepstone_autoapply(request)
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Try apply attempt mode. Default is dry-run scan.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
