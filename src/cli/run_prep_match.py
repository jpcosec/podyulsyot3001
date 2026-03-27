"""Backward-compatible alias for `src.cli.run_pipeline`."""

from __future__ import annotations

from src.cli.run_pipeline import (  # noqa: F401
    _default_checkpoint_path,
    _failed_summary_state,
    _load_dotenv_if_present,
    _load_profile_evidence,
    _profile_base_to_evidence,
    _write_run_summary_artifact,
    _write_verification_artifact,
    main,
)


if __name__ == "__main__":
    raise SystemExit(main())
