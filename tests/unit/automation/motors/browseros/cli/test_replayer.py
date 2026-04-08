"""Pure tests for BrowserOS replayer using replay contracts."""

from __future__ import annotations

from pathlib import Path
import pytest

from src.automation.ariadne.contracts import (
    ReplayAction,
    ReplayObserve,
    ReplayPath,
    ReplayStep,
    ReplayTarget,
)
from src.automation.ariadne.exceptions import (
    FormReviewRequired,
    HumanInterventionRequired,
)
from src.automation.motors.browseros.cli.client import SnapshotElement
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

    def navigate(self, url: str, page_id: int):
        self.calls.append(("navigate", url, page_id))

    def upload_file(self, page_id: int, element_id: int, file_path: Path):
        self.calls.append(("upload_file", page_id, element_id, str(file_path)))

    def search_dom(self, page_id: int, selector: str) -> list[int]:
        self.calls.append(("search_dom", page_id, selector))
        return [99]  # Mock ID


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
    target = ReplayTarget(text="CV_english.pdf")
    assert executor._resolve_element_id(snapshot, target) == 1


def test_assert_observation_raises_on_missing_snapshot_text():
    executor = BrowserOSReplayer(_FakeClient())
    observe = ReplayObserve(required_elements=[ReplayTarget(text="Missing")])
    with pytest.raises(BrowserOSObserveError):
        executor._assert_observation(
            _snapshot((1, "button", "Continue")), observe, "missing", page_id=1
        )


def test_run_executes_ariadne_path():
    path = ReplayPath(
        id="test_path",
        task_id="test_task",
        steps=[
            ReplayStep(
                step_index=1,
                name="step1",
                description="desc1",
                observe=ReplayObserve(required_elements=[ReplayTarget(text="Submit")]),
                actions=[
                    ReplayAction(intent="click", target=ReplayTarget(text="Submit"))
                ],
            )
        ],
    )
    client = _FakeClient(
        [_snapshot((1, "button", "Submit")), _snapshot((1, "button", "Submit"))]
    )
    executor = BrowserOSReplayer(client)

    result = executor.run(
        page_id=1,
        path=path,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=None,
        dry_run=False,
    )

    assert result.status == "submitted"
    assert ("click", 1, 1) in client.calls


def test_dry_run_stops_at_guard():
    path = ReplayPath(
        id="test_path",
        task_id="test_task",
        steps=[
            ReplayStep(
                step_index=1,
                name="step1",
                description="desc1",
                observe=ReplayObserve(),
                actions=[
                    ReplayAction(intent="click", target=ReplayTarget(text="Submit"))
                ],
                dry_run_stop=True,
            )
        ],
    )
    client = _FakeClient([_snapshot((1, "button", "Submit"))])
    executor = BrowserOSReplayer(client)

    result = executor.run(
        page_id=1,
        path=path,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=None,
        dry_run=True,
    )

    assert result.status == "dry_run"
    assert ("click", 1, 1) not in client.calls


def test_execute_action_uses_fallback():
    client = _FakeClient(
        [
            _snapshot((2, "button", "Secondary")),  # for primary check
            _snapshot((2, "button", "Secondary")),  # for fallback execution
        ]
    )
    executor = BrowserOSReplayer(client)

    action = ReplayAction(
        intent="click",
        target=ReplayTarget(text="Primary"),
        fallback=ReplayAction(intent="click", target=ReplayTarget(text="Secondary")),
    )

    executor._execute_action(
        page_id=1,
        action=action,
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=None,
        fields_filled=[],
    )

    assert ("click", 1, 2) in client.calls


def test_execute_action_navigates_with_rendered_template():
    client = _FakeClient()
    executor = BrowserOSReplayer(client)

    executor._execute_action(
        page_id=7,
        action=ReplayAction(intent="navigate", value="{{job.url}}"),
        context={"job": {"url": "https://example.test/apply"}},
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=None,
        fields_filled=[],
    )

    assert ("navigate", "https://example.test/apply", 7) in client.calls


def test_execute_single_step_routes_upload_letter_to_letter_path():
    client = _FakeClient(
        [
            _snapshot((5, "input", "Upload cover letter")),
            _snapshot((5, "input", "Upload cover letter")),
        ]
    )
    executor = BrowserOSReplayer(client)

    executor.execute_single_step(
        page_id=3,
        step=ReplayStep(
            step_index=1,
            name="upload_letter",
            description="Upload the cover letter",
            observe=ReplayObserve(
                required_elements=[ReplayTarget(text="Upload cover letter")]
            ),
            actions=[
                ReplayAction(
                    intent="upload_letter",
                    target=ReplayTarget(text="Upload cover letter"),
                )
            ],
        ),
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=Path("/tmp/letter.pdf"),
    )

    assert ("upload_file", 3, 5, "/tmp/letter.pdf") in client.calls


def test_execute_single_step_rejects_upload_letter_without_letter_path():
    client = _FakeClient(
        [
            _snapshot((5, "input", "Upload cover letter")),
            _snapshot((5, "input", "Upload cover letter")),
        ]
    )
    executor = BrowserOSReplayer(client)

    with pytest.raises(ValueError, match="upload_letter action requires letter_path"):
        executor.execute_single_step(
            page_id=3,
            step=ReplayStep(
                step_index=1,
                name="upload_letter",
                description="Upload the cover letter",
                observe=ReplayObserve(
                    required_elements=[ReplayTarget(text="Upload cover letter")]
                ),
                actions=[
                    ReplayAction(
                        intent="upload_letter",
                        target=ReplayTarget(text="Upload cover letter"),
                    )
                ],
            ),
            context={},
            cv_path=Path("/tmp/cv.pdf"),
            letter_path=None,
        )


def test_execute_single_step_skips_optional_upload_letter_without_letter_path():
    client = _FakeClient(
        [
            _snapshot((5, "input", "Upload cover letter")),
            _snapshot((5, "input", "Upload cover letter")),
        ]
    )
    executor = BrowserOSReplayer(client)

    executor.execute_single_step(
        page_id=3,
        step=ReplayStep(
            step_index=1,
            name="upload_letter",
            description="Upload the cover letter",
            observe=ReplayObserve(
                required_elements=[ReplayTarget(text="Upload cover letter")]
            ),
            actions=[
                ReplayAction(
                    intent="upload_letter",
                    target=ReplayTarget(text="Upload cover letter"),
                    optional=True,
                )
            ],
        ),
        context={},
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=None,
    )

    assert ("upload_file", 3, 5, "/tmp/letter.pdf") not in client.calls


def test_execute_single_step_raises_hitl_request_for_human_required_steps():
    client = _FakeClient([_snapshot((1, "button", "Continue"))])
    executor = BrowserOSReplayer(client)

    with pytest.raises(HumanInterventionRequired, match="Need approval") as exc:
        executor.execute_single_step(
            page_id=1,
            step=ReplayStep(
                step_index=2,
                name="review",
                description="Need approval",
                observe=ReplayObserve(),
                actions=[],
                human_required=True,
            ),
            context={},
            cv_path=Path("/tmp/cv.pdf"),
        )

    assert exc.value.reason == "human_required"


def test_execute_single_step_converts_observation_failure_to_hitl_request():
    client = _FakeClient([_snapshot((1, "button", "Continue"))])
    executor = BrowserOSReplayer(client)

    with pytest.raises(HumanInterventionRequired) as exc:
        executor.execute_single_step(
            page_id=1,
            step=ReplayStep(
                step_index=1,
                name="login_wall",
                description="Login required",
                observe=ReplayObserve(required_elements=[ReplayTarget(text="Sign in")]),
                actions=[],
            ),
            context={},
            cv_path=Path("/tmp/cv.pdf"),
        )

    assert exc.value.reason == "observation_failed"


def test_execute_single_step_analyzes_form_and_fills_known_fields():
    client = _FakeClient(
        [
            _snapshot(
                (1, "text", "First name"),
                (2, "input", "First name"),
                (3, "text", "Email"),
                (4, "input", "Email"),
                (5, "text", "Resume"),
                (6, "input", "Resume"),
            ),
            _snapshot(
                (1, "text", "First name"),
                (2, "input", "First name"),
                (3, "text", "Email"),
                (4, "input", "Email"),
                (5, "text", "Resume"),
                (6, "input", "Resume"),
            ),
            _snapshot(
                (1, "text", "First name"),
                (2, "input", "First name"),
                (3, "text", "Email"),
                (4, "input", "Email"),
                (5, "text", "Resume"),
                (6, "input", "Resume"),
            ),
            _snapshot(
                (1, "text", "First name"),
                (2, "input", "First name"),
                (3, "text", "Email"),
                (4, "input", "Email"),
                (5, "text", "Resume"),
                (6, "input", "Resume"),
            ),
            _snapshot(
                (1, "text", "First name"),
                (2, "input", "First name"),
                (3, "text", "Email"),
                (4, "input", "Email"),
                (5, "text", "Resume"),
                (6, "input", "Resume"),
            ),
        ]
    )
    executor = BrowserOSReplayer(client)

    executor.execute_single_step(
        page_id=9,
        step=ReplayStep(
            step_index=1,
            name="analyze_form",
            description="Analyze and fill the form",
            observe=ReplayObserve(),
            actions=[ReplayAction(intent="analyze_form")],
        ),
        context={"profile": {"first_name": "Ada", "email": "ada@example.com"}},
        cv_path=Path("/tmp/cv.pdf"),
    )

    assert ("fill", 9, 2, "Ada") in client.calls
    assert ("fill", 9, 4, "ada@example.com") in client.calls
    assert ("upload_file", 9, 6, "/tmp/cv.pdf") in client.calls


def test_execute_single_step_analyze_form_raises_review_for_unknown_required_fields():
    client = _FakeClient(
        [
            _snapshot(
                (1, "text", "Employee code"),
                (2, "input", "Employee code"),
            ),
            _snapshot(
                (1, "text", "Employee code"),
                (2, "input", "Employee code"),
            ),
        ]
    )
    executor = BrowserOSReplayer(client)

    executor._form_analyzer.analyze_browseros_snapshot = (
        lambda _elements: executor._form_analyzer.analyze_generic_elements(  # type: ignore[method-assign]
            [
                {
                    "id": "employee-code",
                    "type": "input",
                    "label": "Employee code",
                    "selector": "#employee-code",
                    "required": True,
                }
            ]
        )
    )

    with pytest.raises(FormReviewRequired, match="requires human review") as exc:
        executor.execute_single_step(
            page_id=1,
            step=ReplayStep(
                step_index=1,
                name="analyze_form",
                description="Analyze the form",
                observe=ReplayObserve(),
                actions=[ReplayAction(intent="analyze_form")],
            ),
            context={"profile": {}},
            cv_path=Path("/tmp/cv.pdf"),
        )

    assert "Employee code" in exc.value.details["summary"]


def test_execute_single_step_analyze_form_raises_review_for_unknown_browseros_field():
    client = _FakeClient(
        [
            _snapshot(
                (1, "text", "Employee code"),
                (2, "input", "Employee code"),
            ),
            _snapshot(
                (1, "text", "Employee code"),
                (2, "input", "Employee code"),
            ),
        ]
    )
    executor = BrowserOSReplayer(client)

    with pytest.raises(FormReviewRequired, match="requires human review") as exc:
        executor.execute_single_step(
            page_id=1,
            step=ReplayStep(
                step_index=1,
                name="analyze_form",
                description="Analyze the form",
                observe=ReplayObserve(),
                actions=[ReplayAction(intent="analyze_form")],
            ),
            context={"profile": {}},
            cv_path=Path("/tmp/cv.pdf"),
        )

    assert "browser snapshot field semantics unknown" in exc.value.details["summary"]
