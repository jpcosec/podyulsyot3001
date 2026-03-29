"""CLI entry point for the document generation pipeline.

Generates tailored CV, motivation letter, and email body for a job application
based on approved matches written by the match skill.

Reads approved match artifacts from ``output/match_skill/<source>/<job_id>/``
and writes rendered documents to ``output/<source>/<job_id>/nodes/generate_documents/``.

Usage::

    python -m src.generate_documents.main \\
        --source stepstone --job-id 12345

    # With optional context overrides
    python -m src.generate_documents.main \\
        --source stepstone --job-id 12345 \\
        --profile data/profile/base_profile.json \\
        --city Berlin --receiver-name "Prof. Müller"

CLI arguments are defined in ``_build_parser()``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.ai.generate_documents.graph import (
    build_default_generate_documents_chain,
    _default_profile_base_data,
    generate_documents_bundle,
)
from src.core.data_manager import DataManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate tailored application documents from approved match artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", required=True, help="Job portal source name (e.g. stepstone)."
    )
    parser.add_argument(
        "--job-id", required=True, dest="job_id", help="Unique job posting identifier."
    )
    parser.add_argument(
        "--profile",
        help="Path to profile base data JSON. Defaults to data/reference_data/profile/base_profile/profile_base_data.json",
    )

    ctx = parser.add_argument_group("document context overrides")
    ctx.add_argument("--city", default=None, help="City for the letter header.")
    ctx.add_argument(
        "--receiver-name", dest="receiver_name", default=None, help="Recipient name."
    )
    ctx.add_argument(
        "--receiver-department",
        dest="receiver_department",
        default=None,
        help="Recipient department.",
    )
    ctx.add_argument(
        "--receiver-institution",
        dest="receiver_institution",
        default=None,
        help="Recipient institution.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run document generation for an approved match. Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    state: dict[str, Any] = {"source": args.source, "job_id": args.job_id}
    data_manager = DataManager()

    if args.profile:
        try:
            profile_base_data = json.loads(
                Path(args.profile).read_text(encoding="utf-8")
            )
            profile_ref = data_manager.write_json_artifact(
                source=args.source,
                job_id=args.job_id,
                node_name="pipeline_inputs",
                stage="proposed",
                filename="profile_base_data.json",
                data=profile_base_data,
            )
            state.setdefault("artifact_refs", {})["profile_base_data"] = str(
                profile_ref
            )
        except FileNotFoundError:
            parser.error(f"profile file not found: {args.profile}")
        except json.JSONDecodeError as exc:
            parser.error(f"invalid JSON in {args.profile}: {exc}")

    for key in ("city", "receiver_name", "receiver_department", "receiver_institution"):
        if value := getattr(args, key):
            state[key] = value

    try:
        chain = build_default_generate_documents_chain()
        requirements_state = data_manager.read_json_artifact(
            source=args.source,
            job_id=args.job_id,
            node_name="extract_bridge",
            stage="proposed",
            filename="state.json",
        )
        approved_state = data_manager.read_json_artifact(
            source=args.source,
            job_id=args.job_id,
            node_name="match_skill",
            stage="approved",
            filename="state.json",
        )
        if state.get("artifact_refs", {}).get("profile_base_data"):
            profile_base = data_manager.read_json_artifact(
                source=args.source,
                job_id=args.job_id,
                node_name="pipeline_inputs",
                stage="proposed",
                filename="profile_base_data.json",
            )
        else:
            profile_path = Path(
                "data/reference_data/profile/base_profile/profile_base_data.json"
            )
            if profile_path.exists():
                profile_base = json.loads(profile_path.read_text(encoding="utf-8"))
            else:
                profile_base = _default_profile_base_data()
        if not profile_base:
            profile_base = _default_profile_base_data()

        approved_state_path = data_manager.artifact_path(
            source=args.source,
            job_id=args.job_id,
            node_name="match_skill",
            stage="approved",
            filename="state.json",
        )
        from src.ai.match_skill.storage import MatchArtifactStore

        source_hash = MatchArtifactStore(data_manager.jobs_root).sha256_file(
            approved_state_path
        )
        deltas, rendered, review_assist = generate_documents_bundle(
            source=args.source,
            job_id=args.job_id,
            chain=chain,
            profile_base=profile_base,
            approved_matches_raw=approved_state.get("matches", []),
            requirements_raw=requirements_state.get("requirements", []),
            review_items=[],
            approved_state_hash=source_hash,
            state=state,
        )

        refs = {
            "document_deltas_ref": str(
                data_manager.write_json_artifact(
                    source=args.source,
                    job_id=args.job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="deltas.json",
                    data=deltas.model_dump(),
                )
            ),
            "cv_markdown_ref": str(
                data_manager.write_text_artifact(
                    source=args.source,
                    job_id=args.job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="cv.md",
                    content=rendered.cv_markdown,
                )
            ),
            "letter_markdown_ref": str(
                data_manager.write_text_artifact(
                    source=args.source,
                    job_id=args.job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="cover_letter.md",
                    content=rendered.letter_markdown,
                )
            ),
            "email_markdown_ref": str(
                data_manager.write_text_artifact(
                    source=args.source,
                    job_id=args.job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="email_body.txt",
                    content=rendered.email_markdown,
                )
            ),
            "review_assist_ref": str(
                data_manager.write_json_artifact(
                    source=args.source,
                    job_id=args.job_id,
                    node_name="generate_documents",
                    stage="review",
                    filename="assist.json",
                    data=review_assist.model_dump(),
                )
            ),
        }

        output = {
            "status": "documents_generated",
            "artifact_refs": refs,
        }
        print(json.dumps(output, indent=2))
        return 0

    except Exception as exc:
        print(f"[Fatal] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
