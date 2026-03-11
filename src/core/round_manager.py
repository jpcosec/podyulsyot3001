"""Round artifact manager for immutable review iteration storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class RoundManager:
    """Manage immutable `round_<NNN>` artifacts for match review."""

    def __init__(self, job_dir: str | Path):
        self.job_dir = Path(job_dir)
        self.review_dir = self.job_dir / "nodes" / "match" / "review"
        self.rounds_dir = self.review_dir / "rounds"
        self.rounds_dir.mkdir(parents=True, exist_ok=True)

    def get_latest_round(self) -> int:
        rounds = [
            round_n
            for path in self.rounds_dir.glob("round_*")
            if path.is_dir()
            for round_n in [self._parse_round_name(path.name)]
            if round_n is not None
        ]
        return max(rounds) if rounds else 0

    def create_next_round(self) -> int:
        round_n = self.get_latest_round() + 1
        self.ensure_round(round_n)
        return round_n

    def ensure_round(self, round_n: int) -> Path:
        round_dir = self.get_round_dir(round_n)
        round_dir.mkdir(parents=True, exist_ok=True)
        return round_dir

    def get_round_dir(self, round_n: int) -> Path:
        if round_n < 1:
            raise ValueError("round_n must be >= 1")
        return self.rounds_dir / f"round_{round_n:03d}"

    def save_artifact(self, round_n: int, filename: str, content: str) -> Path:
        round_dir = self.ensure_round(round_n)
        path = round_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def save_json(
        self, round_n: int, filename: str, payload: Mapping[str, Any]
    ) -> Path:
        return self.save_artifact(
            round_n,
            filename,
            json.dumps(dict(payload), indent=2, ensure_ascii=False),
        )

    def load_feedback(self, round_n: int) -> dict[str, Any] | None:
        path = self.get_round_dir(round_n) / "feedback.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data

    def get_latest_feedback(self) -> dict[str, Any] | None:
        latest = self.get_latest_round()
        if latest < 1:
            return None
        return self.load_feedback(latest)

    def get_all_feedback_patches(self) -> list[dict[str, str]]:
        patches: list[dict[str, str]] = []
        for round_n in range(1, self.get_latest_round() + 1):
            feedback = self.load_feedback(round_n)
            if not isinstance(feedback, Mapping):
                continue
            items = feedback.get("feedback")
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, Mapping):
                    continue
                patch = item.get("patch_evidence")
                if not isinstance(patch, Mapping):
                    continue
                patch_id = str(patch.get("id", "")).strip()
                description = str(patch.get("description", "")).strip()
                if patch_id and description:
                    patches.append({"id": patch_id, "description": description})
        return patches

    @staticmethod
    def _parse_round_name(name: str) -> int | None:
        if not name.startswith("round_"):
            return None
        suffix = name.removeprefix("round_")
        if not suffix.isdigit():
            return None
        return int(suffix)
