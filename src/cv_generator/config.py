from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CVConfig:
    project_root: Path
    profile_root: Path
    pipeline_root: Path

    @classmethod
    def from_defaults(cls) -> "CVConfig":
        cv_root = Path(__file__).resolve().parent
        project_root = cv_root.parent.parent
        return cls(
            project_root=project_root,
            profile_root=project_root
            / "data"
            / "reference_data"
            / "profile"
            / "base_profile",
            pipeline_root=project_root / "data" / "pipelined_data",
        )

    def profile_path(self) -> Path:
        return self.profile_root / "profile_base_data.json"

    def cv_render_dir(self, source: str, job_id: str, via: str = "") -> Path:
        base = self.pipeline_root / source / job_id / "cv" / "rendered"
        if via:
            return base / via
        return base
