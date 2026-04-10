"""Vim-inspired HITL review screen for document content (HITL 3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.message import Message
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    LoadingIndicator,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from src.review_ui.bus import MatchBus
from src.review_ui.document_parser import (
    DocType,
    DocumentSegment,
    ParsedDocument,
    parse_bundle,
)


class EditorMode(Enum):
    NORMAL = auto()
    VISUAL = auto()


@dataclass
class LineAnnotation:
    """An annotation attached to a document segment."""
    segment_id: str
    action: str  # "delete" | "replace" | "comment" | "insert_after"
    new_value: Optional[str] = None
    feedback: Optional[str] = None


class AnnotationModal(ModalScreen[Optional[Dict[str, str]]]):
    """Modal for creating/editing an annotation."""

    def __init__(
        self,
        action: str,
        initial_value: str = "",
        prompt: str = "Edit text:",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.action = action
        self.initial_value = initial_value
        self.prompt = prompt

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(f"[bold]{self.action.upper()}[/] - {self.prompt}")
            yield TextArea(self.initial_value, id="annotation-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def on_save(self) -> None:
        self.dismiss({"value": self.query_one("#annotation-input", TextArea).text})

    @on(Button.Pressed, "#btn-cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    def on_mount(self) -> None:
        self.query_one("#annotation-input").focus()


class DocEditor(Static, can_focus=True):
    """Vim-mode editor for a single document."""

    class ModeChanged(Message):
        def __init__(self, mode: EditorMode) -> None:
            super().__init__()
            self.mode = mode

    class AnnotationCreated(Message):
        def __init__(self, annotation: LineAnnotation) -> None:
            super().__init__()
            self.annotation = annotation

    def __init__(self, doc: ParsedDocument, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.doc = doc
        self.cursor_line = 0
        self.anchor_line: Optional[int] = None
        self.mode = EditorMode.NORMAL
        self.annotations: Dict[str, LineAnnotation] = {}

    def render(self) -> str:
        lines = []
        for i, line in enumerate(self.doc.all_lines):
            prefix = "  "
            style = ""

            # Selection range
            if self.mode == EditorMode.VISUAL and self.anchor_line is not None:
                lo, hi = (
                    min(self.anchor_line, self.cursor_line),
                    max(self.anchor_line, self.cursor_line),
                )
                if lo <= i <= hi:
                    style = "on blue"

            # Cursor
            if i == self.cursor_line:
                prefix = "> "
                if not style:
                    style = "reverse"

            # Annotation marker
            seg = self.doc.segment_for_line(i)
            if seg and seg.segment_id in self.annotations:
                ann = self.annotations[seg.segment_id]
                marker = (
                    "✎"
                    if ann.action == "replace"
                    else "✗" if ann.action == "delete" else "💬"
                )
                line = f"{line} [yellow]{marker}[/]"

            if style:
                lines.append(f"[{style}]{prefix}{line}[/]")
            else:
                lines.append(f"{prefix}{line}")

        return "\n".join(lines)

    def on_key(self, event: Any) -> None:
        if self.mode == EditorMode.NORMAL:
            if event.key == "j":
                self.cursor_line = min(self.cursor_line + 1, len(self.doc.all_lines) - 1)
            elif event.key == "k":
                self.cursor_line = max(self.cursor_line - 1, 0)
            elif event.key == "v":
                self.mode = EditorMode.VISUAL
                self.anchor_line = self.cursor_line
                self.post_message(self.ModeChanged(self.mode))
            elif event.key == "d":
                self._annotate_selected("delete")
            elif event.key == "c":
                self._annotate_selected("replace")
        elif self.mode == EditorMode.VISUAL:
            if event.key == "j":
                self.cursor_line = min(self.cursor_line + 1, len(self.doc.all_lines) - 1)
            elif event.key == "k":
                self.cursor_line = max(self.cursor_line - 1, 0)
            elif event.key == "escape":
                self.mode = EditorMode.NORMAL
                self.anchor_line = None
                self.post_message(self.ModeChanged(self.mode))
            elif event.key == "d":
                self._annotate_selected("delete")
            elif event.key == "c":
                self._annotate_selected("replace")
        
        self.refresh()

    def _annotate_selected(self, action: str) -> None:
        if self.mode == EditorMode.VISUAL and self.anchor_line is not None:
            segs = self.doc.segments_in_range(self.anchor_line, self.cursor_line)
        else:
            seg = self.doc.segment_for_line(self.cursor_line)
            segs = [seg] if seg else []

        if not segs: return

        # For simplicity in this TUI, we annotate the first segment in the range
        # True span selection is hard, so we follow the design of segment-level annotation
        target_seg = segs[0]
        
        if action == "delete":
            self.annotations[target_seg.segment_id] = LineAnnotation(target_seg.segment_id, "delete")
            self.notify(f"Deleted {target_seg.segment_id}")
            self.mode = EditorMode.NORMAL
            self.anchor_line = None
        elif action == "replace":
            def apply_replace(result: Optional[Dict[str, str]]) -> None:
                if result:
                    self.annotations[target_seg.segment_id] = LineAnnotation(
                        target_seg.segment_id, "replace", new_value=result["value"]
                    )
                    self.notify("Replacement saved")
                self.mode = EditorMode.NORMAL
                self.anchor_line = None
                self.refresh()

            self.app.push_screen(AnnotationModal("replace", target_seg.raw_text), apply_replace)


class ContentReviewScreen(Screen):
    """Interactive HITL review screen for generated content."""

    BINDINGS = [
        ("s", "submit", "Submit review"),
        ("q", "quit_screen", "Back"),
    ]

    DEFAULT_CSS = """
    ContentReviewScreen {
        layout: grid;
        grid-size: 1;
    }

    #header-panel {
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $accent;
    }

    #editor-container {
        height: 1fr;
    }

    DocEditor {
        height: auto;
        padding: 1 2;
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

    #modal-container {
        width: 80%;
        height: 80%;
        padding: 1 2;
        background: $panel;
        border: thick $accent;
        align: center middle;
    }

    #annotation-input {
        height: 1fr;
        margin: 1 0;
    }

    #modal-buttons {
        height: auto;
        align: right middle;
    }

    #modal-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, bus: MatchBus, source: str, job_id: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self._source = source
        self._job_id = job_id
        self._surface: Any | None = None
        self._docs: Dict[DocType, ParsedDocument] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Loading content ...", id="header-panel")
        
        with TabbedContent(id="editor-tabs"):
            with TabPane("CV", id="tab-cv"):
                yield ScrollableContainer(id="cv-scroll")
            with TabPane("Letter", id="tab-letter"):
                yield ScrollableContainer(id="letter-scroll")
            with TabPane("Email", id="tab-email"):
                yield ScrollableContainer(id="email-scroll")

        with Horizontal(id="action-bar"):
            yield Label("[dim]Mode: NORMAL | j/k: navigate, v: visual, d: delete, c: replace[/]  ", id="mode-label")
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
        self._docs = parse_bundle(surface.payload)
        
        self.query_one("#header-panel", Label).update(
            f"[bold]Content Review[/]  ·  {self._source}/{self._job_id}"
        )
        
        # Add editors to panes
        self.query_one("#cv-scroll").mount(DocEditor(self._docs["cv"], id="editor-cv"))
        self.query_one("#letter-scroll").mount(DocEditor(self._docs["letter"], id="editor-letter"))
        self.query_one("#email-scroll").mount(DocEditor(self._docs["email"], id="editor-email"))
        
        self.query_one("#editor-cv").focus()

    @on(DocEditor.ModeChanged)
    def on_mode_changed(self, event: DocEditor.ModeChanged) -> None:
        msg = "VISUAL | escape: cancel, d: delete, c: replace" if event.mode == EditorMode.VISUAL else "NORMAL | j/k: navigate, v: visual, d: delete, c: replace"
        self.query_one("#mode-label", Label).update(f"[dim]Mode: {msg}[/]  ")

    def action_submit(self) -> None:
        if not self._surface: return
        
        # Reconstruct modified markdown per doc
        patches = []
        
        for dtype in ["cv", "letter", "email"]:
            doc = self._docs[dtype]  # type: ignore
            editor = self.query_one(f"#editor-{dtype}", DocEditor)
            if not editor.annotations:
                continue
                
            # Build modified text
            parts = []
            for seg in doc.segments:
                if seg.segment_id in editor.annotations:
                    ann = editor.annotations[seg.segment_id]
                    if ann.action == "delete":
                        continue
                    if ann.action == "replace":
                        parts.append(ann.new_value)
                else:
                    parts.append(seg.raw_text)
            
            field_name = "cv_full_md" if dtype == "cv" else "letter_full_md" if dtype == "letter" else "email_body_md"
            patches.append({
                "action": "modify",
                "target_id": field_name,
                "new_value": "\n\n".join(parts)
            })
            
        self._do_submit(patches)

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
