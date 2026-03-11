"""Tests for immutable review round artifact management."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.round_manager import RoundManager


def test_create_next_round_is_incremental(tmp_path: Path) -> None:
    manager = RoundManager(tmp_path / "job")
    first = manager.create_next_round()
    second = manager.create_next_round()

    assert first == 1
    assert second == 2
    assert manager.get_round_dir(1).exists()
    assert manager.get_round_dir(2).exists()


def test_get_all_feedback_patches_reads_patch_evidence(tmp_path: Path) -> None:
    manager = RoundManager(tmp_path / "job")
    round_n = manager.create_next_round()
    manager.save_artifact(
        round_n,
        "feedback.json",
        json.dumps(
            {
                "round_n": 1,
                "feedback": [
                    {
                        "req_id": "R1",
                        "action": "patch",
                        "reviewer_note": "Add EEG thesis evidence",
                        "patch_evidence": {
                            "id": "P_EMERGENTE_EEG_01",
                            "description": "EEG thesis with Python/MNE",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
    )

    patches = manager.get_all_feedback_patches()

    assert patches == [
        {
            "id": "P_EMERGENTE_EEG_01",
            "description": "EEG thesis with Python/MNE",
        }
    ]
