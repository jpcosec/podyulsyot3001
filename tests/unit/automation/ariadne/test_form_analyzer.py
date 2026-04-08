"""Unit tests for the Ariadne form analyzer."""

from __future__ import annotations

from src.automation.ariadne.form_analyzer import (
    AriadneFormAnalyzer,
    BrowserOSFieldElement,
)


def test_analyze_browseros_snapshot_maps_known_fields():
    analyzer = AriadneFormAnalyzer()
    form = analyzer.analyze_browseros_snapshot(
        [
            BrowserOSFieldElement(1, "text", "First name"),
            BrowserOSFieldElement(2, "input", "First name"),
            BrowserOSFieldElement(3, "text", "Email"),
            BrowserOSFieldElement(4, "input", "Email"),
            BrowserOSFieldElement(5, "text", "Resume"),
            BrowserOSFieldElement(6, "input", "Resume"),
        ]
    )

    actions = form.to_ariadne_actions()
    assert [field.semantic_key for field in form.fields] == [
        "first_name",
        "email",
        "cv",
    ]
    assert [action.intent.value for action in actions] == ["fill", "fill", "upload"]
    assert actions[0].value == "{{profile.first_name}}"
    assert actions[1].value == "{{profile.email}}"
    assert actions[2].value is None


def test_analyze_generic_elements_requires_review_for_unknown_required_fields():
    analyzer = AriadneFormAnalyzer()
    form = analyzer.analyze_generic_elements(
        [
            {
                "id": "mystery",
                "type": "input",
                "label": "Internal employee code",
                "selector": "#employee-code",
                "required": True,
            }
        ]
    )

    assert form.requires_review() is True
    assert "required field semantics unknown" in form.review_summary()


def test_analyze_generic_elements_requires_review_for_unsafe_fields():
    analyzer = AriadneFormAnalyzer()
    form = analyzer.analyze_generic_elements(
        [
            {
                "id": "salary",
                "type": "input",
                "label": "Expected salary",
                "selector": "#salary",
                "required": False,
            }
        ]
    )

    assert form.requires_review() is True
    assert "unsafe field" in form.review_summary()


def test_analyze_browseros_snapshot_requires_review_for_unknown_fields():
    analyzer = AriadneFormAnalyzer()
    form = analyzer.analyze_browseros_snapshot(
        [
            BrowserOSFieldElement(1, "text", "Employee code"),
            BrowserOSFieldElement(2, "input", "Employee code"),
        ]
    )

    assert form.requires_review() is True
    assert "browser snapshot field semantics unknown" in form.review_summary()
