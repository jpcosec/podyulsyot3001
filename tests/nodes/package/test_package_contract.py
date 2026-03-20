from __future__ import annotations

import pytest

from src.nodes.package.contract import PackageInputState, PackagedArtifact


def test_package_input_state_requires_non_empty_values() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        PackageInputState.model_validate({"source": "tu_berlin", "job_id": ""})


def test_packaged_artifact_requires_sha256_prefix() -> None:
    with pytest.raises(ValueError, match="sha256"):
        PackagedArtifact.model_validate({"path": "final/cv.md", "sha256": "bad"})
