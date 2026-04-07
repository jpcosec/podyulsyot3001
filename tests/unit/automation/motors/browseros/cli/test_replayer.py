"""Pure tests for BrowserOS replayer using Ariadne models."""

from __future__ import annotations

from pathlib import Path
import pytest

from src.automation.ariadne.models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadnePath,
    AriadneStep,
    AriadneTarget,
)
from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement
from src.automation.motors.browseros.cli.replayer import (
    BrowserOSObserveError,
    BrowserOSReplayer,
)


class _FakeClient:
    def __init__(self, snapshots=None):
        self.snapshots = list(snapshots or [])
        self.calls = []

    def take_snapshot(self, page_id: int):
        self.calls.append(("take_snapshot", page_id))
        return self.snapshots.pop(0) if self.snapshots else []

    def click(self, page_id: int, element_id: int):
        self.calls.append(("click", page_id, element_id))

    def fill(self, page_id: int, element_id: int, value: str):
        self.calls.append(("fill", page_id, element_id, value))

    def navigate(self, page_id: int, url: str):
        self.calls.append(("navigate", page_id, url))

    def upload_file(self, page_id: int, element_id: int, file_path: Path):
        self.calls.append(("upload_file", page_id, element_id, str(file_path)))

    def search_dom(self, page_id: int, selector: str) -> list[int]:
        self.calls.append(("search_dom", page_id, selector))
        return [99] # Mock ID


def _snapshot(*items):
    return [
        SnapshotElement(
            element_id=element_id, element_type=element_type, text=text, raw_line=""
        )
        for element_id, element_type, text in items
    ]


def test_render_template_resolves_nested_context_values():
    executor = BrowserOSReplayer(_FakeClient())
    rendered = executor.render_template(
        "Hello {{profile.first_name}} {{profile.last_name}}",
        {"profile": {"first_name": "Ada", "last_name": "Lovelace"}},
    )
    assert "Ada Lovelace" in rendered


def test_resolve_element_id_supports_partial_matches():
    executor = BrowserOSReplayer(_FakeClient())
    snapshot = _snapshot((1, "button", "Seleccionar resume CV_english.pdf"))
    target = AriadneTarget(text="CV_english.pdf")
    assert executor._resolve_element_id(snapshot, target) == 1


def test_assert_observation_raises_on_missing_snapshot_text():
    executor = BrowserOSReplayer(_FakeClient())
    observe = AriadneObserve(required_elements=[AriadneTarget(text="Missing")])
    with pytest.raises(BrowserOSObserveError):
        executor._assert_observation(
            _snapshot((1, "button", "Continue")),
            observe,
            "missing",
            page_id=1
        )


def test_run_executes_ariadne_path():
    path = AriadnePath(
        id="test_path",
        task_id="test_task",
        steps=[
            AriadneStep(
                step_index=1,
                name="step1",
                description="desc1",
                observe=AriadneObserve(required_elements=[AriadneTarget(text="Submit")]),
                actions=[
                    AriadneAction(intent=AriadneIntent.CLICK, target=AriadneTarget(text="Submit"))
                ]
            )
        ]
    )
    client = _FakeClient([_snapshot((1, "button", "Submit")), _snapshot((1, "button", "Submit"))])
    executor = BrowserOSReplayer(client)

    result = executor.run(
        page_id=1,
        path=path,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        dry_run=False,
    )

    assert result.status == "submitted"
    assert ("click", 1, 1) in client.calls


def test_dry_run_stops_at_guard():
    path = AriadnePath(
        id="test_path",
        task_id="test_task",
        steps=[
            AriadneStep(
                step_index=1,
                name="step1",
                description="desc1",
                observe=AriadneObserve(),
                actions=[AriadneAction(intent=AriadneIntent.CLICK, target=AriadneTarget(text="Submit"))],
                dry_run_stop=True
            )
        ]
    )
    client = _FakeClient([_snapshot((1, "button", "Submit"))])
    executor = BrowserOSReplayer(client)

    result = executor.run(
        page_id=1,
        path=path,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        dry_run=True,
    )

    assert result.status == "dry_run"
    assert ("click", 1, 1) not in client.calls


def test_execute_action_uses_fallback():
    client = _FakeClient([
        _snapshot((2, "button", "Secondary")), # for primary check
        _snapshot((2, "button", "Secondary"))  # for fallback execution
    ])
    executor = BrowserOSReplayer(client)
    
    action = AriadneAction(
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(text="Primary"),
        fallback=AriadneAction(
            intent=AriadneIntent.CLICK,
            target=AriadneTarget(text="Secondary")
        )
    )

    executor._execute_action(
        page_id=1,
        action=action,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        fields_filled=[]
    )

    assert ("click", 1, 2) in client.calls
