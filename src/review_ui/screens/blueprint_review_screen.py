"""Master-detail HITL review screen for job blueprint (HITL 2)."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    RichLog,
    Static,
)

from src.review_ui.bus import MatchBus


class IntentEditModal(ModalScreen[str]):
    """Modal screen for editing section intent."""

    def __init__(self, initial_value: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.initial_value = initial_value

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label("[bold]Edit Section Intent[/]")
            yield Input(value=self.initial_value, id="intent-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def on_save(self) -> None:
        self.dismiss(self.query_one("#intent-input", Input).value)

    @on(Button.Pressed, "#btn-cancel")
    def on_cancel(self) -> None:
        self.dismiss(self.initial_value)

    def on_mount(self) -> None:
        self.query_one("#intent-input").focus()


class BlueprintReviewScreen(Screen):
    """Interactive HITL review screen for the section blueprint."""

    BINDINGS = [
        ("j", "cursor_down", "Next section"),
        ("k", "cursor_up", "Prev section"),
        ("e", "edit_intent", "Edit intent"),
        ("x", "toggle_drop", "Drop/Keep"),
        ("s", "submit", "Submit review"),
        ("q", "quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    BlueprintReviewScreen {
        layout: grid;
        grid-size: 1;
    }

    #header-panel {
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $accent;
    }

    #main-container {
        height: 1fr;
        layout: horizontal;
    }

    #section-list {
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

    .section-item {
        padding: 0 1;
    }

    .status-dropped { color: $error; text-style: strike; }
    .status-modified { color: $warning; }

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

    #modal-container {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $panel;
        border: thick $accent;
        align: center middle;
    }

    #modal-buttons {
        margin-top: 1;
        align: right middle;
    }

    #modal-buttons Button {
        margin-left: 1;
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
        self._sections: list[dict[str, Any]] = []
        self._modified_sections: list[dict[str, Any]] = []
        self._dropped_ids: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Loading blueprint ...", id="header-panel")
        
        with Horizontal(id="main-container"):
            yield ListView(id="section-list")
            with ScrollableContainer(id="detail-panel"):
                yield LoadingIndicator(id="loading", classes="visible")
                yield Static("", id="detail-content")

        with Horizontal(id="action-bar"):
            yield Button("Submit (s)", id="btn-submit", variant="success")
            
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
            self.app.call_from_thread(self.notify, f"Load failed: {exc}", severity="error")

    def _render_surface(self, surface: Any) -> None:
        self._surface = surface
        self._sections = surface.payload.get("sections", [])
        # Deep copy for local modifications
        import copy
        self._modified_sections = copy.deepcopy(self._sections)
        
        self.query_one("#header-panel", Label).update(
            f"[bold]Blueprint Review[/]  ·  {self._source}/{self._job_id}"
        )
        
        self._refresh_list()
        self.query_one("#loading").remove_class("visible")
        if self._modified_sections:
            self.query_one("#section-list", ListView).index = 0
            self._update_detail(0)

    def _refresh_list(self) -> None:
        list_view = self.query_one("#section-list", ListView)
        curr_idx = list_view.index
        list_view.clear()
        for section in self._modified_sections:
            sec_id = section.get("section_id", "")
            is_dropped = sec_id in self._dropped_ids
            label = sec_id
            if is_dropped:
                label = f"[status-dropped]{sec_id} [DROPPED][/]"
            list_view.append(ListItem(Label(label), classes="section-item"))
        list_view.index = curr_idx

    def _update_detail(self, index: int) -> None:
        if not (0 <= index < len(self._modified_sections)):
            return
            
        section = self._modified_sections[index]
        sec_id = section.get("section_id", "")
        intent = section.get("section_intent", "")
        tot = section.get("logical_train_of_thought", [])
        
        content = (
            f"[bold]Section: {sec_id}[/]\n\n"
            f"[accent]Intent:[/]\n{intent}\n\n"
            f"[accent]Logical Train of Thought:[/]\n{', '.join(map(str, tot))}\n\n"
            f"[dim]Actions: [e] edit intent, [x] drop/keep[/]"
        )
        self.query_one("#detail-content", Static).update(content)

    @on(ListView.Selected)
    def _on_item_selected(self, event: ListView.Selected) -> None:
        self._update_detail(self.query_one("#section-list", ListView).index or 0)

    def action_cursor_down(self) -> None:
        self.query_one("#section-list", ListView).index += 1

    def action_cursor_up(self) -> None:
        self.query_one("#section-list", ListView).index -= 1

    def action_edit_intent(self) -> None:
        idx = self.query_one("#section-list", ListView).index
        if idx is not None:
            initial = self._modified_sections[idx].get("section_intent", "")
            def check_result(new_intent: str) -> None:
                if new_intent != initial:
                    self._modified_sections[idx]["section_intent"] = new_intent
                    self._update_detail(idx)
                    self.notify("Intent updated")
            
            self.app.push_screen(IntentEditModal(initial), check_result)

    def action_toggle_drop(self) -> None:
        idx = self.query_one("#section-list", ListView).index
        if idx is not None:
            sec_id = self._modified_sections[idx].get("section_id", "")
            if sec_id in self._dropped_ids:
                self._dropped_ids.remove(sec_id)
                self.notify(f"Section {sec_id} restored")
            else:
                self._dropped_ids.add(sec_id)
                self.notify(f"Section {sec_id} dropped")
            self._refresh_list()

    def action_submit(self) -> None:
        if not self._surface: return
        
        # Filter out dropped sections
        final_sections = [
            s for s in self._modified_sections 
            if s.get("section_id") not in self._dropped_ids
        ]
        
        patch = {
            "action": "modify",
            "target_id": "sections",
            "new_value": final_sections
        }
        
        self._do_submit([patch])

    @work(thread=True, exit_on_error=False)
    def _do_submit(self, patches: list[dict[str, Any]]) -> None:
        self.app.call_from_thread(setattr, self.query_one("#btn-submit", Button), "disabled", True)
        self.app.call_from_thread(setattr, self.query_one("#status-log", RichLog), "display", True)
        
        try:
            result = self._bus.resume_with_review("approve", patches=patches)
            status = result.get("status", "done")
            self.app.call_from_thread(self.query_one("#status-log", RichLog).write, f"[green]Success: {status}[/]")
            self.app.call_from_thread(self.action_quit_screen)
        except Exception as e:
            self.app.call_from_thread(self.query_one("#status-log", RichLog).write, f"[red]Error: {e}[/]")
            self.app.call_from_thread(setattr, self.query_one("#btn-submit", Button), "disabled", False)

    def action_quit_screen(self) -> None:
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()
