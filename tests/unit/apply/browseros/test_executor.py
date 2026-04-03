"""Pure tests for BrowserOS playbook execution helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.apply.browseros_client import SnapshotElement
from src.apply.browseros_executor import (
    BrowserOSObserveError,
    BrowserOSPlaybookExecutor,
)
from src.apply.browseros_models import BrowserOSPlaybook, ExpectedElement


class _FakeClient:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.calls = []

    def take_snapshot(self, page_id: int):
        self.calls.append(("take_snapshot", page_id))
        return self.snapshots.pop(0)

    def click(self, page_id: int, element_id: int):
        self.calls.append(("click", page_id, element_id))

    def fill(self, page_id: int, element_id: int, value: str):
        self.calls.append(("fill", page_id, element_id, value))

    def select_option(self, page_id: int, element_id: int, value: str):
        self.calls.append(("select_option", page_id, element_id, value))

    def upload_file(self, page_id: int, element_id: int, file_path: Path):
        self.calls.append(("upload_file", page_id, element_id, str(file_path)))

    def evaluate_script_react(self, page_id: int, selector: str, value: str):
        self.calls.append(("evaluate_script_react", page_id, selector, value))


def _snapshot(*items):
    return [
        SnapshotElement(
            element_id=element_id, element_type=element_type, text=text, raw_line=""
        )
        for element_id, element_type, text in items
    ]


def test_render_template_resolves_nested_context_values():
    executor = BrowserOSPlaybookExecutor(_FakeClient([]))
    rendered = executor.render_template(
        "Hello {{profile.first_name}} {{profile.last_name}}",
        {"profile": {"first_name": "Ada", "last_name": "Lovelace"}},
    )
    assert rendered == "Hello Ada Lovelace"


def test_resolve_element_id_supports_partial_matches():
    executor = BrowserOSPlaybookExecutor(_FakeClient([]))
    snapshot = _snapshot((1, "button", "Seleccionar resume CV_english.pdf"))
    assert (
        executor._resolve_element_id(snapshot, "Seleccionar resume CV_english.pdf") == 1
    )


def test_assert_expected_elements_raises_on_missing_snapshot_text():
    executor = BrowserOSPlaybookExecutor(_FakeClient([]))
    with pytest.raises(BrowserOSObserveError):
        executor._assert_expected_elements(
            _snapshot((1, "button", "Continue")),
            [ExpectedElement(text="Missing", type="button")],
            "missing",
        )


def test_run_skips_unresolved_prefill_actions_and_stops_at_dry_run():
    playbook = BrowserOSPlaybook.model_validate_json(
        Path("src/apply/playbooks/linkedin_easy_apply_v1.json").read_text(
            encoding="utf-8"
        )
    )
    client = _FakeClient(
        [
            _snapshot(
                (1, "textbox", "First name"),
                (2, "textbox", "Last name"),
                (3, "textbox", "Mobile phone number"),
                (4, "combobox", "Email address"),
            ),
            _snapshot((10, "button", "Ir al siguiente paso")),
            _snapshot(
                (11, "button", "Descargar resume"),
                (12, "radio", "Seleccionar resume CV_english.pdf"),
                (13, "button", "Boton para cargar curriculum"),
            ),
            _snapshot((12, "radio", "Seleccionar resume CV_english.pdf")),
            _snapshot((14, "button", "Ir al siguiente paso")),
            _snapshot(
                (15, "button", "Edite la siguiente entrada de experiencia"),
                (16, "button", "Add more"),
            ),
            _snapshot((17, "button", "Ir al siguiente paso")),
            _snapshot((18, "button", "Revisar tu solicitud")),
            _snapshot((19, "button", "Revisar tu solicitud")),
            _snapshot(
                (20, "button", "Editar Informacion de contacto"),
                (21, "button", "Editar Curriculum"),
                (22, "button", "Editar Work experience"),
                (23, "button", "Enviar solicitud"),
            ),
        ]
    )
    executor = BrowserOSPlaybookExecutor(client, input_func=lambda _: "y")

    result = executor.run(
        page_id=99,
        playbook=playbook,
        context={
            "profile": {},
            "cv_filename": "CV_english.pdf",
            "cv_path": "/tmp/CV_english.pdf",
        },
        cv_path=Path("/tmp/CV_english.pdf"),
        dry_run=True,
    )

    assert result.status == "dry_run"
    assert ("click", 99, 12) in client.calls
    assert all(call[0] != "fill" for call in client.calls)


def test_execute_action_uses_fallback_when_primary_selector_missing():
    client = _FakeClient(
        [
            _snapshot((13, "button", "Boton para cargar curriculum")),
            _snapshot((13, "button", "Boton para cargar curriculum")),
        ]
    )
    executor = BrowserOSPlaybookExecutor(client)
    playbook = BrowserOSPlaybook.model_validate_json(
        Path("src/apply/playbooks/linkedin_easy_apply_v1.json").read_text(
            encoding="utf-8"
        )
    )
    action = playbook.steps[1].actions[0]

    executor._execute_action(
        page_id=7,
        action=action,
        context={"cv_filename": "CV_english.pdf", "cv_path": "/tmp/CV_english.pdf"},
        cv_path=Path("/tmp/CV_english.pdf"),
        fields_filled=[],
    )

    assert ("upload_file", 7, 13, "/tmp/CV_english.pdf") in client.calls


def test_conditional_human_required_prompts_operator():
    playbook = BrowserOSPlaybook.model_validate(
        {
            "meta": {
                "source": "linkedin",
                "flow": "easy_apply",
                "version": "v1",
                "recorded": "2026-04-01",
                "total_steps": 1,
                "status": "draft",
            },
            "entry_point": {},
            "path": "test.path",
            "steps": [
                {
                    "step": 1,
                    "name": "questions",
                    "description": "Conditional review",
                    "observe": {
                        "expected_elements": [{"text": "Continue", "type": "button"}]
                    },
                    "actions": [],
                    "human_required": "conditional",
                }
            ],
        }
    )
    client = _FakeClient([_snapshot((1, "button", "Continue"))])
    prompts = []
    executor = BrowserOSPlaybookExecutor(
        client,
        input_func=lambda message: prompts.append(message) or "y",
    )

    result = executor.run(
        page_id=3,
        playbook=playbook,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        dry_run=False,
    )

    assert result.status == "submitted"
    assert prompts
