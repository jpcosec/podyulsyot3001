"""Master-detail HITL review screen for match evidence (HITL 1)."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    RichLog,
    Static,
)

from src.review_ui.bus import MatchBus


class MatchReviewScreen(Screen):
    """Interactive HITL review screen for requirement-to-profile matches."""

    BINDINGS = [
        ("j", "cursor_down", "Next match"),
        ("k", "cursor_up", "Prev match"),
        ("y", "approve_selected", "Approve (y)"),
        ("n", "reject_selected", "Reject (n)"),
        ("space", "toggle_selected", "Toggle (space)"),
        ("a", "approve_all", "Approve All"),
        ("r", "reject_all", "Reject All"),
        ("s", "submit", "Submit review"),
        ("q", "quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    MatchReviewScreen {
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

    #main-container {
        height: 1fr;
        layout: horizontal;
    }

    #match-list {
        width: 30;
        height: 1fr;
        border-right: solid $panel;
        background: $surface;
    }

    #detail-panel {
        width: 1fr;
        height: 1fr;
        padding: 1 2;
    }

    .match-item {
        padding: 0 1;
    }

    .match-item Label {
        width: 100%;
    }

    .status-approved { color: $success; }
    .status-rejected { color: $error; }
    .status-pending { color: $text-muted; }

    .score-high { color: $success; }
    .score-medium { color: $warning; }
    .score-low { color: $error; }

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

    .detail-label {
        color: $accent;
        text-style: bold;
        margin-top: 1;
    }

    .detail-text {
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        bus: MatchBus,
        source: str,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self._source = source
        self._job_id = job_id
        self._surface: Any | None = None
        self._matches: list[dict[str, Any]] = []
        self._outcomes: dict[str, str] = {}  # req_id -> "approve" | "reject" | "pending"
        self._requirement_lookup: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        yield Label("Loading match evidence ...", id="header-panel")
        yield Label("", id="summary-bar")
        
        with Horizontal(id="main-container"):
            yield ListView(id="match-list")
            with ScrollableContainer(id="detail-panel"):
                yield LoadingIndicator(id="loading", classes="visible")
                yield Static("", id="detail-content")

        with Horizontal(id="action-bar"):
            yield Button("Approve All (a)", id="btn-approve-all", variant="primary")
            yield Button("Reject All (r)", id="btn-reject-all", variant="error")
            yield Button("Submit (s)", id="btn-submit", variant="success")
            
        yield RichLog(id="status-log", markup=True)
        yield Footer()

    def on_mount(self) -> None:
        """Start loading data."""
        self._load_data()

    @work(thread=True, exit_on_error=False)
    def _load_data(self) -> None:
        try:
            surface = self._bus.load_current_review_surface(self._source, self._job_id)
            self.app.call_from_thread(self._render_surface, surface)
        except Exception as exc:
            self.app.call_from_thread(self.notify, f"Load failed: {exc}", severity="error")

    def _render_surface(self, surface: Any) -> None:
        self._surface = surface
        payload = surface.payload
        self._matches = payload.get("matches", [])
        
        job_kg = payload.get("job_kg", {})
        job_delta = payload.get("job_delta", {})
        job_title = (
            job_kg.get("job_title_english")
            or job_delta.get("job_title_english")
            or "Unknown Job"
        )

        # Build requirement lookup
        self._requirement_lookup = {}
        for req in job_kg.get("hard_requirements", []):
            self._requirement_lookup[req.get("id", "")] = req.get("text", "")
        for req in job_kg.get("soft_context", []):
            self._requirement_lookup[req.get("id", "")] = req.get("text", "")

        # Initialize outcomes
        self._outcomes = {m.get("requirement_id", ""): "pending" for m in self._matches}

        # Update UI
        self.query_one("#header-panel", Label).update(
            f"[bold]Match Evidence Review[/]  ·  {self._source}/{self._job_id}"
        )
        self._update_summary(job_title)
        
        # Populate list
        list_view = self.query_one("#match-list", ListView)
        list_view.clear()
        for match in self._matches:
            req_id = match.get("requirement_id", "")
            score = match.get("match_score", 0)
            list_view.append(self._create_list_item(req_id, score))

        self.query_one("#loading").remove_class("visible")
        if self._matches:
            list_view.index = 0
            self._update_detail(0)

    def _get_item_label(self, req_id: str, score: float) -> str:
        """Calculate the rich text label for a match item."""
        outcome = self._outcomes.get(req_id, "pending")
        icon = "○"
        if outcome == "approve":
            icon = "✓"
        elif outcome == "reject":
            icon = "✗"

        status_class = f"status-{outcome}"
        score_class = (
            "score-high"
            if score >= 0.8
            else "score-medium" if score >= 0.5 else "score-low"
        )

        return f"[{status_class}]{icon}[/] {req_id} [{score_class}]{score:.0%}[/]"

    def _create_list_item(self, req_id: str, score: float) -> ListItem:
        label = self._get_item_label(req_id, score)
        return ListItem(Label(label), classes="match-item")

    def _update_summary(self, job_title: str) -> None:
        total = len(self._matches)
        approved = sum(1 for o in self._outcomes.values() if o == "approve")
        rejected = sum(1 for o in self._outcomes.values() if o == "reject")
        pending = total - approved - rejected
        
        summary = (
            f"[bold]{job_title}[/]\n"
            f"[green]✓ {approved}[/] approved  [red]✗ {rejected}[/] rejected  [dim]○ {pending}[/] pending  ·  "
            f"[bold]{total}[/] total"
        )
        self.query_one("#summary-bar", Label).update(summary)

    def _update_detail(self, index: int) -> None:
        if not (0 <= index < len(self._matches)):
            return
            
        match = self._matches[index]
        req_id = match.get("requirement_id", "")
        req_text = self._requirement_lookup.get(req_id, "[text not found]")
        evidence = ", ".join(match.get("profile_evidence_ids", [])) or "[no evidence]"
        reasoning = match.get("reasoning", "")
        
        content = (
            f"[bold]Requirement {req_id}[/]\n\n"
            f"[accent]Requirement Text:[/]\n{req_text}\n\n"
            f"[accent]Evidence:[/]\n{evidence}\n\n"
            f"[accent]Reasoning:[/]\n{reasoning}\n\n"
            f"[dim]Actions: [y] approve, [n] reject, [space] toggle[/]"
        )
        self.query_one("#detail-content", Static).update(content)

    @on(ListView.Selected)
    def _on_item_selected(self, event: ListView.Selected) -> None:
        self._update_detail(self.query_one("#match-list", ListView).index or 0)

    def action_cursor_down(self) -> None:
        self.query_one("#match-list", ListView).index += 1

    def action_cursor_up(self) -> None:
        self.query_one("#match-list", ListView).index -= 1

    def action_approve_selected(self) -> None:
        idx = self.query_one("#match-list", ListView).index
        if idx is not None:
            self._set_outcome(idx, "approve")

    def action_reject_selected(self) -> None:
        idx = self.query_one("#match-list", ListView).index
        if idx is not None:
            self._set_outcome(idx, "reject")

    def action_toggle_selected(self) -> None:
        idx = self.query_one("#match-list", ListView).index
        if idx is not None:
            req_id = self._matches[idx].get("requirement_id", "")
            current = self._outcomes.get(req_id, "pending")
            new_outcome = "reject" if current == "approve" else "approve"
            self._set_outcome(idx, new_outcome)

    def _set_outcome(self, index: int, outcome: str) -> None:
        req_id = self._matches[index].get("requirement_id", "")
        self._outcomes[req_id] = outcome

        # Refresh list item
        list_view = self.query_one("#match-list", ListView)
        score = self._matches[index].get("match_score", 0)
        label_text = self._get_item_label(req_id, score)
        list_view.children[index].query_one(Label).update(label_text)

        # Update summary
        job_kg = self._surface.payload.get("job_kg", {})
        job_delta = self._surface.payload.get("job_delta", {})
        job_title = (
            job_kg.get("job_title_english")
            or job_delta.get("job_title_english")
            or "Job"
        )
        self._update_summary(job_title)

        # Auto-advance
        if index < len(self._matches) - 1:
            list_view.index += 1

    def action_approve_all(self) -> None:
        for req_id in self._outcomes:
            self._outcomes[req_id] = "approve"
        self._refresh_all()

    def action_reject_all(self) -> None:
        for req_id in self._outcomes:
            self._outcomes[req_id] = "reject"
        self._refresh_all()

    def _refresh_all(self) -> None:
        list_view = self.query_one("#match-list", ListView)
        for i, match in enumerate(self._matches):
            req_id = match.get("requirement_id", "")
            score = match.get("match_score", 0)
            label_text = self._get_item_label(req_id, score)
            list_view.children[i].query_one(Label).update(label_text)
        
        job_kg = self._surface.payload.get("job_kg", {})
        job_delta = self._surface.payload.get("job_delta", {})
        job_title = job_kg.get("job_title_english") or job_delta.get("job_title_english") or "Job"
        self._update_summary(job_title)

    def action_submit(self) -> None:
        if not self._surface: return
        
        # Build patches (FIX for bug #5)
        patches = []
        for req_id, outcome in self._outcomes.items():
            if outcome != "pending":
                patches.append({
                    "action": outcome,
                    "target_id": req_id
                })
        
        self._do_submit(patches)

    @work(thread=True, exit_on_error=False)
    def _do_submit(self, patches: list[dict[str, Any]]) -> None:
        self.app.call_from_thread(setattr, self.query_one("#btn-submit", Button), "disabled", True)
        self.app.call_from_thread(setattr, self.query_one("#status-log", RichLog), "display", True)
        self.app.call_from_thread(self.query_one("#status-log", RichLog).write, "[yellow]Submitting review...[/]")
        
        try:
            # We use "approve" as bulk action if most are approved, or just "approve" as sentinel
            # The individual patches carry the real weight
            result = self._bus.resume_with_review("approve", patches=patches)
            status = result.get("status", "done")
            self.app.call_from_thread(self.query_one("#status-log", RichLog).write, f"[green]Success: {status}[/]")
            # Return to explorer after success
            self.app.call_from_thread(self.action_quit_screen)
        except Exception as e:
            self.app.call_from_thread(self.query_one("#status-log", RichLog).write, f"[red]Error: {e}[/]")
            self.app.call_from_thread(setattr, self.query_one("#btn-submit", Button), "disabled", False)

    def action_quit_screen(self) -> None:
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()
