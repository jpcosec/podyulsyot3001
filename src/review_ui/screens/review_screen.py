"""HITL review screen for the match skill TUI.

This screen is the HITL gate: it loads the persisted ``ReviewSurface`` from the
``MatchArtifactStore``, renders one ``MatchRow`` per requirement, and lets the
reviewer submit a complete ``ReviewPayload`` back to the LangGraph thread.
"""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, LoadingIndicator, RichLog

from src.core.ai.match_skill.contracts import (
    ProfileEvidence,
    ReviewDecision,
    ReviewItemDecision,
    ReviewPayload,
    ReviewSurface,
    ReviewSurfaceItem,
)
from src.review_ui.bus import MatchBus
from src.review_ui.widgets.match_row import MatchRow


class ReviewScreen(Screen):
    """Interactive HITL review screen.

    Displays the match proposal from the persisted ``ReviewSurface`` and
    allows the operator to submit decisions per requirement.  On submission,
    the screen resumes the paused LangGraph thread via ``MatchBus``.

    Args:
        bus: ``MatchBus`` instance providing async I/O with LangGraph + disk.
        source: Source identifier used to locate artifacts.
        job_id: Job identifier used to locate artifacts.
    """

    BINDINGS = [
        ("ctrl+a", "approve_all", "Approve all"),
        ("ctrl+r", "reject_all", "Reject all"),
        ("s", "submit", "Submit review"),
        ("q", "quit_screen", "Quit"),
    ]

    DEFAULT_CSS = """
    ReviewScreen {
        layout: grid;
        grid-size: 1;
    }

    #header-panel {
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $accent;
    }

    #summary-line {
        color: $text-muted;
    }

    #recommendation-badge {
        text-style: bold;
    }

    #rows-container {
        height: 1fr;
        overflow-y: auto;
    }

    #action-bar {
        height: auto;
        layout: horizontal;
        padding: 1 2;
        background: $panel;
        border-top: solid $accent;
        align: right middle;
    }

    #status-log {
        height: 5;
        border-top: solid $panel;
        background: $surface;
        display: none;
    }

    #status-log.visible {
        display: block;
    }

    #loading {
        display: none;
    }

    #loading.visible {
        display: block;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        bus: MatchBus,
        source: str,
        job_id: str,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self._source = source
        self._job_id = job_id
        self._surface: ReviewSurface | None = None
        # Accumulates per-row decisions keyed by requirement_id
        self._decisions: dict[str, MatchRow.DecisionChanged] = {}

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Compose the review screen layout and action controls."""
        yield Header()
        yield Label("Loading review surface …", id="header-panel")
        with ScrollableContainer(id="rows-container"):
            yield LoadingIndicator(id="loading", classes="visible")
        with Horizontal(id="action-bar"):
            yield Button("✓ Approve all", id="btn-approve-all", variant="default")
            yield Button("✗ Reject all", id="btn-reject-all", variant="error")
            yield Button("Submit review »", id="btn-submit", variant="success")
        yield RichLog(id="status-log", markup=True)
        yield Footer()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        """Start loading the current review surface when the screen mounts."""
        self._load_surface()

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    @work(thread=True, exit_on_error=False)
    def _load_surface(self) -> None:
        """Load the review surface from disk in a background thread."""
        try:
            surface = self._bus.load_current_review_surface(self._source, self._job_id)
            self.app.call_from_thread(self._render_surface, surface)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._show_error, f"{type(exc).__name__}: {exc}")

    @work(thread=True, exit_on_error=False)
    def _submit_review(self, payload: ReviewPayload) -> None:
        """Submit the review payload to LangGraph in a background thread."""
        self.app.call_from_thread(self._disable_submit)
        self.app.call_from_thread(
            self.query_one("#status-log", RichLog).write,
            "[yellow]Submitting review to LangGraph…[/]",
        )
        try:
            result = self._bus.resume_with_review(payload)
            status = (
                result.get("status", "unknown") if isinstance(result, dict) else "done"
            )
            self.app.call_from_thread(
                self.query_one("#status-log", RichLog).write,
                f"[green]Graph resumed — final status: [bold]{status}[/bold][/]",
            )
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(
                self.query_one("#status-log", RichLog).write,
                f"[red]Error: {exc}[/]",
            )
            self.app.call_from_thread(self._re_enable_submit)

    # ------------------------------------------------------------------
    # UI updates (called via call_from_thread)
    # ------------------------------------------------------------------

    def _disable_submit(self) -> None:
        """Disable the submit button to prevent double-submit during submission."""
        btn = self.query_one("#btn-submit", Button)
        btn.disabled = True

    def _re_enable_submit(self) -> None:
        """Re-enable the submit button after a failed submission (allows retry)."""
        btn = self.query_one("#btn-submit", Button)
        btn.disabled = False

    def _render_surface(self, surface: ReviewSurface) -> None:
        """Populate the screen with loaded review surface data."""
        self._surface = surface

        rec_colour = {"proceed": "green", "marginal": "yellow", "reject": "red"}.get(
            surface.recommendation, "white"
        )
        header_panel = self.query_one("#header-panel", Label)
        header_panel.update(
            f"[bold]Round {surface.round_number}[/]  ·  "
            f"Score: [bold]{surface.total_score * 100:.0f}%[/]  ·  "
            f"Recommendation: [{rec_colour}]{surface.recommendation}[/]\n"
            f"[dim]{surface.summary_notes}[/]\n"
            f"[dim]Hash: {surface.source_state_hash}[/]"
        )

        loading = self.query_one("#loading", LoadingIndicator)
        loading.remove_class("visible")

        container = self.query_one("#rows-container", ScrollableContainer)
        for item in surface.items:
            row = MatchRow(item)
            container.mount(row)
            # Initialise decision map with default approve
            self._decisions[item.requirement_id] = MatchRow.DecisionChanged(
                requirement_id=item.requirement_id,
                decision="approve",
                note="",
                patch_evidence=None,
            )

    def _show_error(self, message: str) -> None:
        log = self.query_one("#status-log", RichLog)
        log.add_class("visible")
        log.write(f"[red]Error: {message}[/]")

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    @on(MatchRow.DecisionChanged)
    def _on_row_decision_changed(self, event: MatchRow.DecisionChanged) -> None:
        self._decisions[event.requirement_id] = event

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#btn-approve-all")
    def _on_approve_all(self, _: Button.Pressed) -> None:
        self.action_approve_all()

    @on(Button.Pressed, "#btn-reject-all")
    def _on_reject_all(self, _: Button.Pressed) -> None:
        self.action_reject_all()

    @on(Button.Pressed, "#btn-submit")
    def _on_submit(self, _: Button.Pressed) -> None:
        self.action_submit()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_approve_all(self) -> None:
        """Set all rows to approve."""
        if self._surface is None:
            return
        for item in self._surface.items:
            if not item.in_regeneration_scope:
                continue
            self._decisions[item.requirement_id] = MatchRow.DecisionChanged(
                requirement_id=item.requirement_id,
                decision="approve",
                note="",
                patch_evidence=None,
            )
        self.notify("All rows set to Approve.")

    def action_reject_all(self) -> None:
        """Set all rows to reject."""
        if self._surface is None:
            return
        for item in self._surface.items:
            if not item.in_regeneration_scope:
                continue
            self._decisions[item.requirement_id] = MatchRow.DecisionChanged(
                requirement_id=item.requirement_id,
                decision="reject",
                note="",
                patch_evidence=None,
            )
        self.notify("All rows set to Reject.")

    def action_submit(self) -> None:
        """Validate and submit the review payload to LangGraph."""
        if self._surface is None:
            self.notify("Review surface not loaded yet.", severity="error")
            return

        items: list[ReviewItemDecision] = []
        for req_id, decision_msg in self._decisions.items():
            items.append(
                ReviewItemDecision(
                    requirement_id=req_id,
                    decision=decision_msg.decision,
                    note=decision_msg.note,
                    patch_evidence=decision_msg.patch_evidence,
                )
            )

        if not items:
            self.notify("No decisions recorded.", severity="warning")
            return

        payload = ReviewPayload(
            source_state_hash=self._surface.source_state_hash,
            items=items,
        )
        log = self.query_one("#status-log", RichLog)
        log.add_class("visible")
        self._submit_review(payload)

    def action_quit_screen(self) -> None:
        """Pop this screen or quit the app."""
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()
