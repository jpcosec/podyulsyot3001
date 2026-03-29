"""Widget representing a single requirement match row in the review UI.

Each ``MatchRow`` is a self-contained widget that holds and reacts to a
``ReviewItemDecision`` for one requirement.  Decision changes are surfaced as
the ``MatchRow.DecisionChanged`` message so the parent screen can aggregate
all row states into a ``ReviewPayload``.
"""

from __future__ import annotations

from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Static

from src.ai.match_skill.contracts import ProfileEvidence, ReviewDecision, ReviewSurfaceItem

# Colours mapped to match statuses and decisions
_STATUS_COLOUR: dict[str, str] = {
    "matched": "green",
    "partial": "yellow",
    "missing": "red",
}

_DECISION_COLOUR: dict[str, str] = {
    "approve": "green",
    "request_regeneration": "yellow",
    "reject": "red",
}


class MatchRow(Widget):
    """Interactive widget for one requirement × match result row.

    Reactive state drives visual updates when the reviewer changes their
    decision, so colour badges, patch-evidence inputs, etc. update without
    any manual DOM manipulation.

    Args:
        item: The ``ReviewSurfaceItem`` for this row.
        id: Optional widget id (defaults to the requirement id).
    """

    DEFAULT_CSS = """
    MatchRow {
        height: auto;
        border: solid $panel;
        margin: 0 1 1 1;
        padding: 1 2;
    }

    MatchRow .row-header {
        layout: horizontal;
        height: auto;
    }

    MatchRow .req-text {
        width: 1fr;
        text-wrap: wrap;
        color: $text;
    }

    MatchRow .score-badge {
        width: auto;
        min-width: 8;
        text-align: right;
    }

    MatchRow .status-label {
        width: auto;
        min-width: 10;
        padding: 0 1;
    }

    MatchRow .evidence-block {
        color: $text-muted;
        margin-top: 1;
        text-wrap: wrap;
        padding-left: 2;
    }

    MatchRow .reasoning-block {
        color: $text-muted;
        margin-top: 0;
        text-wrap: wrap;
        padding-left: 2;
        border-left: solid $accent;
    }

    MatchRow .decision-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
        align: left middle;
    }

    MatchRow #patch-section {
        margin-top: 1;
        display: none;
    }

    MatchRow #patch-section.visible {
        display: block;
    }

    MatchRow Select {
        width: 24;
    }
    """

    # Reactive fields that drive visual updates
    decision: reactive[ReviewDecision] = reactive("approve")

    @dataclass
    class DecisionChanged(Message):
        """Posted when the reviewer changes their decision for this row.

        Attributes:
            requirement_id: The affected requirement.
            decision: New reviewer decision.
            note: Optional note text.
            patch_evidence: Optional evidence patch (only when request_regeneration).
        """

        requirement_id: str
        decision: ReviewDecision
        note: str
        patch_evidence: ProfileEvidence | None

    def __init__(self, item: ReviewSurfaceItem, **kwargs: object) -> None:
        # Use the requirement id as the Textual widget id (must be valid CSS id)
        super().__init__(id=f"row-{item.requirement_id}", **kwargs)
        self._item = item

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        item = self._item
        score_pct = f"{item.score * 100:.0f}%"
        status_colour = _STATUS_COLOUR.get(item.status, "white")
        priority_tag = f" [{item.priority}]" if item.priority else ""

        with Static(classes="row-header"):
            yield Label(
                f"{item.requirement_id}{priority_tag}  {item.requirement_text}",
                classes="req-text",
            )
            yield Label(f"[{status_colour}]{item.status}[/]", classes="status-label")
            yield Label(f"[bold]{score_pct}[/]", classes="score-badge")

        if item.evidence_quotes:
            quote_lines = "\n".join(f'  "{q}"' for q in item.evidence_quotes)
            yield Static(f"Evidence:\n{quote_lines}", classes="evidence-block")

        if item.reasoning:
            yield Static(item.reasoning, classes="reasoning-block")

        if item.in_regeneration_scope:
            with Static(classes="decision-row"):
                yield Select(
                    options=[
                        ("✓ Approve", "approve"),
                        ("↺ Request regeneration", "request_regeneration"),
                        ("✗ Reject", "reject"),
                    ],
                    value="approve",
                    id=f"decision-{item.requirement_id}",
                )
                yield Input(
                    placeholder="Optional reviewer note …",
                    id=f"note-{item.requirement_id}",
                )

            with Static(id="patch-section"):
                yield Label("Patch evidence ID:")
                yield Input(
                    placeholder="evidence id (e.g. ev_python_001)",
                    id=f"patch-id-{item.requirement_id}",
                )
                yield Label("Patch evidence description:")
                yield Input(
                    placeholder="Short description of the additional evidence",
                    id=f"patch-desc-{item.requirement_id}",
                )
        else:
            yield Static(
                "[dim]Not in regeneration scope – decision locked to approve[/]",
                classes="decision-row",
            )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    @on(Select.Changed)
    def _on_select_changed(self, event: Select.Changed) -> None:
        """React to decision dropdown changes."""
        event.stop()
        self.decision = event.value  # type: ignore[assignment]
        self._sync_patch_visibility()
        self._post_decision_changed()

    @on(Input.Changed)
    def _on_input_changed(self, _: Input.Changed) -> None:
        """Re-emit decision message when any input text changes."""
        _.stop()
        self._post_decision_changed()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sync_patch_visibility(self) -> None:
        """Show or hide the patch evidence section based on the decision."""
        patch_section = self.query_one("#patch-section", Static)
        if self.decision == "request_regeneration":
            patch_section.add_class("visible")
        else:
            patch_section.remove_class("visible")

    def _post_decision_changed(self) -> None:
        """Post a ``DecisionChanged`` message with the current widget state."""
        item = self._item
        note = self._safe_input_value(f"note-{item.requirement_id}")
        patch_evidence: ProfileEvidence | None = None

        if self.decision == "request_regeneration":
            patch_id = self._safe_input_value(f"patch-id-{item.requirement_id}")
            patch_desc = self._safe_input_value(f"patch-desc-{item.requirement_id}")
            if patch_id and patch_desc:
                patch_evidence = ProfileEvidence(id=patch_id, description=patch_desc)

        self.post_message(
            self.DecisionChanged(
                requirement_id=item.requirement_id,
                decision=self.decision,
                note=note,
                patch_evidence=patch_evidence,
            )
        )

    def _safe_input_value(self, input_id: str) -> str:
        """Return the value of a child Input widget, or '' if absent."""
        try:
            return self.query_one(f"#{input_id}", Input).value
        except Exception:
            return ""
