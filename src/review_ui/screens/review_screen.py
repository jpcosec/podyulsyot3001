"""HITL review screen for generate_documents_v2 checkpoints."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    RichLog,
    Static,
)

from src.review_ui.bus import MatchBus


class ReviewScreen(Screen):
    """Interactive HITL review screen for one pending checkpoint."""

    BINDINGS = [
        ("a", "approve_all", "Approve All"),
        ("r", "reject_all", "Reject All"),
        ("s", "submit", "Submit review"),
        ("q", "quit_screen", "Quit"),
        ("j", "cursor_down", "Next match"),
        ("k", "cursor_up", "Prev match"),
        ("y", "approve_current", "Yes/Approve"),
        ("n", "reject_current", "No/Reject"),
        ("space", "toggle_current", "Toggle"),
        ("enter", "focus_actions", "Actions"),
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

    #summary-bar {
        height: 3;
        padding: 0 2;
        background: $surface;
        border-bottom: solid $primary;
    }

    #payload-container {
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
    }

    .match-card {
        height: auto;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $primary;
        background: $panel;
    }

    .match-card.selected {
        border: heavy $accent;
    }

    .match-card.approved {
        border-left: solid 3 $success;
    }

    .match-card.rejected {
        border-left: solid 3 $error;
    }

    .match-header {
        height: auto;
        layout: horizontal;
    }

    .match-score {
        width: 8;
        height: auto;
    }

    .match-req {
        width: 1fr;
        height: auto;
    }

    .match-status {
        width: 10;
        height: auto;
    }

    .match-evidence {
        height: auto;
        color: $text-muted;
    }

    .match-reasoning {
        height: auto;
        color: $text;
    }

    .match-requirement {
        height: auto;
        color: $text;
        text-style: bold;
    }

    .match-actions {
        height: auto;
        layout: horizontal;
        align: right middle;
    }

    .match-actions Button {
        margin-left: 1;
    }

    #action-bar {
        height: auto;
        layout: horizontal;
        padding: 1 2;
        background: $panel;
        border-top: solid $accent;
        align: right middle;
    }

    #action-bar Button {
        margin-left: 1;
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

    #payload {
        text-wrap: wrap;
    }

    .selected {
        border: heavy $accent;
    }

    .score-high {
        color: $success;
    }

    .score-medium {
        color: $warning;
    }

    .score-low {
        color: $error;
    }

    .status-pending { color: $text-muted; }
    .status-approved { color: $success; }
    .status-rejected { color: $error; }

    .section-label {
        color: $accent;
        text-style: bold;
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
        self._surface: Any | None = None
        self._selected_action = "approve"
        self._match_outcomes: dict[str, str] = {}
        self._match_edits: dict[str, dict] = {}
        self._matches_data: list[dict] = []
        self._selected_idx: int = 0
        self._requirement_lookup: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Compose the review screen layout and action controls."""
        yield Header()
        yield Label("Loading review surface ...", id="header-panel")
        yield Label("", id="summary-bar")
        with ScrollableContainer(id="payload-container"):
            yield LoadingIndicator(id="loading", classes="visible")
            yield Vertical(id="matches-container")
        with Horizontal(id="action-bar"):
            yield Button(
                "[+] Approve All (a)",
                id="btn-approve",
                variant="primary",
                classes="selected",
            )
            yield Button("[-] Reject All (r)", id="btn-reject", variant="error")
            yield Button("Submit (s)", id="btn-submit", variant="success")
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
    def _submit_review(self, action: str) -> None:
        """Submit the selected review action to LangGraph in a background thread."""
        self.app.call_from_thread(self._disable_submit)
        self.app.call_from_thread(
            self.query_one("#status-log", RichLog).write,
            f"[yellow]Submitting {action} to LangGraph...[/]",
        )
        try:
            result = self._bus.resume_with_review(action)
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

    def _render_surface(self, surface: Any) -> None:
        """Populate the screen with loaded review surface data."""
        self._surface = surface
        header_panel = self.query_one("#header-panel", Label)
        header_panel.update(
            f"[bold]{surface.title}[/]  ·  {self._source}/{self._job_id}\n"
            f"[dim]Stage: {surface.stage}  ·  Artifact: {surface.artifact_stage}[/]"
        )

        payload = surface.payload
        matches = payload.get("matches", [])

        job_kg = payload.get("job_kg", {})
        job_delta = payload.get("job_delta", {})
        job_title = (
            job_kg.get("job_title_english")
            or job_delta.get("job_title_english")
            or "Unknown Job"
        )

        # Build requirement lookup map from job_kg
        self._requirement_lookup: dict[str, str] = {}
        for req in job_kg.get("hard_requirements", []):
            self._requirement_lookup[req.get("id", "")] = req.get("text", "")
        for req in job_kg.get("soft_context", []):
            self._requirement_lookup[req.get("id", "")] = req.get("text", "")

        self._match_outcomes = {m.get("requirement_id", ""): "pending" for m in matches}

        summary = self._build_summary(matches, job_title)
        self.query_one("#summary-bar", Label).update(summary)

        self._render_matches(matches)

        loading = self.query_one("#loading", LoadingIndicator)
        loading.remove_class("visible")

    def _build_summary(self, matches: list[dict], job_title: str) -> str:
        """Build the summary bar with job info and match stats."""
        total = len(matches)
        approved = sum(1 for o in self._match_outcomes.values() if o == "approve")
        rejected = sum(1 for o in self._match_outcomes.values() if o == "reject")
        pending = total - approved - rejected
        high = sum(1 for m in matches if m.get("match_score", 0) >= 0.8)
        medium = sum(1 for m in matches if 0.5 <= m.get("match_score", 0) < 0.8)
        low = sum(1 for m in matches if m.get("match_score", 0) < 0.5)

        return (
            f"[bold]{job_title}[/]\n"
            f"[green]✓ {approved}[/] approved  [red]✗ {rejected}[/] rejected  [dim]○ {pending}[/] pending  ·  "
            f"[green]{high}[/] strong  [yellow]{medium}[/] medium  [red]{low}[/] weak  ·  "
            f"[bold]{total}[/] total"
        )

    def _render_matches(self, matches: list[dict]) -> None:
        """Render each match as a formatted card."""
        self._matches_data = matches if matches else []

        def do_render() -> None:
            try:
                container = self.query_one("#matches-container", Vertical)
            except Exception:
                self.call_later(do_render)
                return

            for child in container.children:
                child.remove()

            for idx, match in enumerate(self._matches_data):
                req_id = match.get("requirement_id", f"R{idx}")
                score = match.get("match_score", 0)
                requirement_text = self._requirement_lookup.get(req_id, "")
                reasoning = match.get("reasoning", "")
                evidence_ids = match.get("profile_evidence_ids", [])

                card = Vertical(classes="match-card", id=f"match-{req_id}")
                children = self.compose_match_card(
                    req_id, score, requirement_text, reasoning, evidence_ids, idx
                )
                container.mount(card)
                for child in children:
                    card.mount(child)

        self.call_later(do_render)

    def compose_match_card(
        self,
        req_id: str,
        score: float,
        requirement: str,
        reasoning: str,
        evidence_ids: list[str],
        idx: int,
    ) -> list[object]:
        """Build children for a match card."""
        score_str = f"{score:.0%}"
        score_class = (
            "score-high"
            if score >= 0.8
            else "score-medium"
            if score >= 0.5
            else "score-low"
        )

        status = self._match_outcomes.get(req_id, "pending")
        status_str = "○ PENDING"
        status_class = "status-pending"
        if status == "approve":
            status_str = "✓ APPROVED"
            status_class = "status-approved"
        elif status == "reject":
            status_str = "✗ REJECTED"
            status_class = "status-rejected"

        evidence_str = ", ".join(evidence_ids) if evidence_ids else "[no evidence]"

        return [
            # Header: ID, Score, Status, Short requirement
            Horizontal(
                Static(f"[{req_id}]", classes="match-id"),
                Static(f"  {score_str}", classes=f"match-score {score_class}"),
                Static(f"  {status_str}", classes=f"match-status {status_class}"),
            ),
            # Full requirement text
            Static(f"📋 Requirement: {requirement}", classes="match-requirement"),
            # Evidence IDs
            Static(f"🔍 Evidence: {evidence_str}", classes="match-evidence"),
            # Reasoning
            Static(f"💭 Reasoning: {reasoning}", classes="match-reasoning"),
            # Action buttons (mouse support)
            Horizontal(
                Button(
                    "✓",
                    id=f"btn-accept-{idx}",
                    variant="primary",
                    compact=True,
                    tooltip="Approve (y)",
                ),
                Button(
                    "✗",
                    id=f"btn-reject-{idx}",
                    variant="error",
                    compact=True,
                    tooltip="Reject (n)",
                ),
                Button(
                    "↔", id=f"btn-toggle-{idx}", compact=True, tooltip="Toggle (space)"
                ),
                id=f"match-actions-{idx}",
            ),
        ]

    def _show_error(self, message: str) -> None:
        log = self.query_one("#status-log", RichLog)
        log.add_class("visible")
        log.write(f"[red]Error: {message}[/]")

    # ------------------------------------------------------------------
    # Message handlers (mouse support)
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#btn-approve")
    def _on_approve(self, _: Button.Pressed) -> None:
        self.action_approve_all()

    @on(Button.Pressed, "#btn-reject")
    def _on_reject(self, _: Button.Pressed) -> None:
        self.action_reject_all()

    @on(Button.Pressed, "#btn-submit")
    def _on_submit(self, _: Button.Pressed) -> None:
        self.action_submit()

    @on(Button.Pressed)
    def _on_match_button(self, event: Button.Pressed) -> None:
        """Handle per-match action buttons (mouse support)."""
        btn_id = event.button.id or ""
        if btn_id.startswith("btn-accept-"):
            idx = int(btn_id.split("-")[-1])
            self._set_match_outcome(idx, "approve")
        elif btn_id.startswith("btn-reject-"):
            idx = int(btn_id.split("-")[-1])
            self._set_match_outcome(idx, "reject")
        elif btn_id.startswith("btn-toggle-"):
            idx = int(btn_id.split("-")[-1])
            current = self._match_outcomes.get(
                self._matches_data[idx].get("requirement_id", ""), "pending"
            )
            new_outcome = "reject" if current == "approve" else "approve"
            self._set_match_outcome(idx, new_outcome)

    # ------------------------------------------------------------------
    # Per-match actions
    # ------------------------------------------------------------------

    def _set_match_outcome(self, idx: int, outcome: str) -> None:
        """Set outcome for a specific match."""
        matches = self._surface.payload.get("matches", [])
        if idx < len(matches):
            req_id = matches[idx].get("requirement_id", f"R{idx}")
            self._match_outcomes[req_id] = outcome
            card = self.query_one(f"#match-{req_id}")

            # Remove all status classes
            card.remove_class("approved")
            card.remove_class("rejected")

            # Add appropriate class and update status text
            status_widget = card.query_one(
                f"#match-actions-{idx}", Horizontal
            ).previous_sibling
            if outcome == "approve":
                card.add_class("approved")
                self.notify(f"[{req_id}] ✓ APPROVED")
            elif outcome == "reject":
                card.add_class("rejected")
                self.notify(f"[{req_id}] ✗ REJECTED")

            # Update summary
            job_title = self._surface.payload.get("job_kg", {}).get(
                "job_title_english", "Job"
            )
            summary = self._build_summary(matches, job_title)
            self.query_one("#summary-bar", Label).update(summary)

    # ------------------------------------------------------------------
    # Keyboard actions
    # ------------------------------------------------------------------

    def action_approve_all(self) -> None:
        """Approve all matches."""
        self._selected_action = "approve"
        for idx, match in enumerate(self._matches_data):
            req_id = match.get("requirement_id", f"R{idx}")
            self._match_outcomes[req_id] = "approve"
        self._sync_action_buttons()
        self._refresh_cards()
        self.notify("All matches APPROVED")

    def action_reject_all(self) -> None:
        """Reject all matches."""
        self._selected_action = "reject"
        for idx, match in enumerate(self._matches_data):
            req_id = match.get("requirement_id", f"R{idx}")
            self._match_outcomes[req_id] = "reject"
        self._sync_action_buttons()
        self._refresh_cards()
        self.notify("All matches REJECTED")

    def action_submit(self) -> None:
        """Validate and submit the review payload to LangGraph."""
        if self._surface is None:
            self.notify("Review surface not loaded yet.", severity="error")
            return

        approved = sum(1 for o in self._match_outcomes.values() if o == "approve")
        rejected = sum(1 for o in self._match_outcomes.values() if o == "reject")
        total = len(self._match_outcomes)

        self.notify(
            f"Submitting: {approved} approved, {rejected} rejected, {total - approved - rejected} pending",
            severity="information",
        )

        log = self.query_one("#status-log", RichLog)
        log.add_class("visible")
        self._submit_review(self._selected_action)

    def action_quit_screen(self) -> None:
        """Pop this screen or quit the app."""
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()

    def action_cursor_down(self) -> None:
        """Move selection to next match."""
        if self._matches_data:
            self._selected_idx = (self._selected_idx + 1) % len(self._matches_data)
            self._highlight_selected()

    def action_cursor_up(self) -> None:
        """Move selection to previous match."""
        if self._matches_data:
            self._selected_idx = (self._selected_idx - 1) % len(self._matches_data)
            self._highlight_selected()

    def action_approve_current(self) -> None:
        """Approve the currently selected match (keyboard shortcut)."""
        if self._matches_data:
            self._set_match_outcome(self._selected_idx, "approve")
            self.notify(f"Match {self._selected_idx + 1} APPROVED (y)")

    def action_reject_current(self) -> None:
        """Reject the currently selected match (keyboard shortcut)."""
        if self._matches_data:
            self._set_match_outcome(self._selected_idx, "reject")
            self.notify(f"Match {self._selected_idx + 1} REJECTED (n)")

    def action_toggle_current(self) -> None:
        """Toggle the current match between approved/rejected."""
        if self._matches_data:
            current = self._match_outcomes.get(
                self._matches_data[self._selected_idx].get("requirement_id", ""),
                "pending",
            )
            new_outcome = "reject" if current == "approve" else "approve"
            self._set_match_outcome(self._selected_idx, new_outcome)
            status = "REJECTED" if new_outcome == "reject" else "APPROVED"
            self.notify(f"Match {self._selected_idx + 1} {status} (space)")

    def action_focus_actions(self) -> None:
        """Focus the action bar for keyboard navigation."""
        self.query_one("#btn-submit", Button).focus()

    def _highlight_selected(self) -> None:
        """Highlight the selected match card."""
        try:
            container = self.query_one("#matches-container", Vertical)
            for idx, child in enumerate(container.children):
                if idx == self._selected_idx:
                    child.add_class("selected")
                else:
                    child.remove_class("selected")
            # Scroll into view
            container.children[self._selected_idx].scroll_visible()
        except Exception:
            pass

    def _refresh_cards(self) -> None:
        """Re-render all cards to show current outcomes."""
        if self._surface:
            matches = self._surface.payload.get("matches", [])
            job_title = self._surface.payload.get("job_kg", {}).get(
                "job_title_english", "Job"
            )
            summary = self._build_summary(matches, job_title)
            self.query_one("#summary-bar", Label).update(summary)
            self._render_matches(matches)

    def _sync_action_buttons(self) -> None:
        """Highlight the currently selected action button."""
        approve = self.query_one("#btn-approve", Button)
        reject = self.query_one("#btn-reject", Button)
        if self._selected_action == "approve":
            approve.add_class("selected")
            reject.remove_class("selected")
        else:
            reject.add_class("selected")
            approve.remove_class("selected")
