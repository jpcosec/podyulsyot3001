"""Binary HITL review screen for profile updates (HITL 4)."""

from __future__ import annotations

from typing import Any, List

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    LoadingIndicator,
    RichLog,
    Static,
)

from src.review_ui.bus import MatchBus


class ProfileDiffScreen(Screen):
    """Interactive HITL review screen for proposed profile updates."""

    BINDINGS = [
        ("a", "approve", "Approve All"),
        ("r", "reject", "Reject All"),
        ("q", "quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    ProfileDiffScreen {
        layout: grid;
        grid-size: 1;
    }

    #header-panel {
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $accent;
    }

    #diff-container {
        height: 1fr;
        padding: 1 2;
    }

    .diff-card {
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        border: solid $primary;
    }

    .diff-path {
        color: $accent;
        text-style: bold;
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
    """

    def __init__(self, bus: MatchBus, source: str, job_id: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self._source = source
        self._job_id = job_id
        self._surface: Any | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Loading profile updates ...", id="header-panel")

        with ScrollableContainer(id="diff-container"):
            yield LoadingIndicator(id="loading", classes="visible")
            yield Static("", id="diff-content")

        with Horizontal(id="action-bar"):
            yield Button("Approve & Persist (a)", id="btn-approve", variant="primary")
            yield Button("Reject (r)", id="btn-reject", variant="error")

        yield RichLog(id="status-log", markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self._load_data()

    @work(thread=True, exit_on_error=False)
    def _load_data(self) -> None:
        try:
            surface = self._bus.load_current_review_surface(self._source, self._job_id)
            self.app.call_from_thread(self._render_surface, surface)
        except Exception as exc:
            self.app.call_from_thread(
                self.notify, f"Load failed: {exc}", severity="error"
            )

    def _render_surface(self, surface: Any) -> None:
        self._surface = surface
        updates = surface.payload.get("updates", [])

        self.query_one("#header-panel", Label).update(
            f"[bold]Profile Update Review[/]  ·  {self._source}/{self._job_id}\n"
            f"[dim]{len(updates)} proposed changes to profile JSON[/]"
        )

        content = []
        for update in updates:
            path = update.get("field_path", "")
            old = update.get("old_value")
            new = update.get("new_value")
            stage = update.get("source_stage", "unknown")

            content.append(f"[bold cyan]Field: {path}[/] [dim](from {stage})[/]")
            content.append(f"[red]- WAS:[/] {old}")
            content.append(f"[green]+ NOW:[/] {new}")
            content.append("-" * 20)

        self.query_one("#diff-content", Static).update("\n".join(content))
        self.query_one("#loading").remove_class("visible")

    def action_approve(self) -> None:
        self._submit_review("approve")

    def action_reject(self) -> None:
        self._submit_review("reject")

    def _submit_review(self, action: str) -> None:
        if not self._surface: return
        self._do_submit(action)

    @work(thread=True, exit_on_error=False)
    def _do_submit(self, action: str) -> None:
        self.app.call_from_thread(setattr, self.query_one("#btn-approve", Button), "disabled", True)
        self.app.call_from_thread(setattr, self.query_one("#btn-reject", Button), "disabled", True)
        self.app.call_from_thread(setattr, self.query_one("#status-log", RichLog), "display", True)
        
        try:
            result = self._bus.resume_with_review(action)
            status = result.get("status", "done")
            self.app.call_from_thread(self.query_one("#status-log", RichLog).write, f"[green]Success: {status}[/]")
            self.app.call_from_thread(self.action_quit_screen)
        except Exception as e:
            self.app.call_from_thread(self.query_one("#status-log", RichLog).write, f"[red]Error: {e}[/]")
            self.app.call_from_thread(setattr, self.query_one("#btn-approve", Button), "disabled", False)
            self.app.call_from_thread(setattr, self.query_one("#btn-reject", Button), "disabled", False)

    def action_quit_screen(self) -> None:
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()
