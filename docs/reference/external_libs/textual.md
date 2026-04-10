# Textual - Terminal UI Framework

Textual is a Python framework for building Terminal User Interfaces (TUIs) with a modern, reactive architecture. It draws inspiration from web development concepts but runs entirely in the terminal.

**Official Resources:**
- GitHub: https://github.com/Textualize/textual
- Documentation: https://textual.textualize.io/
- Discord: https://discord.gg/Enf6Z3qhVr
- Blog: https://textual.textualize.io/blog/

## Core Concepts

### App and Widgets

Textual apps start by subclassing `App`:

```python
from textual.app import App, ComposeResult
from textual.widgets import Button, Label

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Label("Hello, Textual!")
        yield Button("Click me", id="my-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.exit("Button clicked!")
```

- **App** (`textual.app.App`) - Root application class
- **ComposeResult** (`textual.app.ComposeResult`) - Type hint for compose methods
- **Reference**: https://textual.textualize.io/guide/app/

### Reactive Attributes

Reactive attributes automatically trigger UI updates when changed:

```python
from textual.reactive import reactive

class Counter(Widget):
    count = reactive(0)  # Auto-updates UI when changed

    def watch_count(self, value: int) -> None:
        print(f"Count changed to {value}")
```

**Key Features:**
- **Smart refresh** - Auto-updates on change
- **Validation** - `validate_<attr>` methods
- **Watch methods** - `watch_<attr>` for side effects
- **Compute methods** - `compute_<attr>` for derived values
- **Reference**: https://textual.textualize.io/guide/reactivity/

### CSS Styling

Textual uses CSS-like syntax (`.tcss` files):

```python
CSS_PATH = "app.tcss"
# or
CSS = """
Screen {
    background: $surface;
}
Button {
    margin: 1;
}
"""
```

- **Reference**: https://textual.textualize.io/guide/CSS/

### Events and Messages

Handle user input with event handlers:

```python
def on_mount(self) -> None:       # Called when widget mounts
def on_key(self, event: Key) -> None:  # Key press handler
def on_click(self, event: Click) -> None:  # Mouse click

# Use @on decorator for selective handling
from textual import on

@on(Button.Pressed, "#my-button")
def handle_button(self) -> None:
    pass
```

- **Reference**: https://textual.textualize.io/guide/events/

### Actions

Bind keys to reusable actions:

```python
class MyApp(App):
    BINDINGS = [
        ("a", "do_something", "Do Something"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def action_do_something(self) -> None:
        pass
```

- **Reference**: https://textual.textualize.io/guide/actions/

### Screens

Navigate between different views:

```python
class MyScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("My Screen")

# Push screen
self.push_screen(MyScreen())

# Pop screen
self.pop_screen()

# Push screen with result callback (modal pattern)
def on_result(value: str | None) -> None:
    if value:
        self.notify(f"Got: {value}")

self.push_screen(MyScreen(), on_result)

# Inside the screen: dismiss with a return value
self.dismiss("some result")   # triggers the callback above
# or just close without a value
self.dismiss()
```

- **Reference**: https://textual.textualize.io/guide/screens/

### Workers

Run async or threaded tasks without blocking UI:

```python
from textual.work import work

# Async worker (for I/O-bound tasks)
@work
async def fetch_data(self) -> None:
    result = await self._api_call()
    self.post_message(self.DataReady(result))

# Thread worker (for sync/CPU-bound tasks, e.g. LangGraph runs)
@work(thread=True)
def run_pipeline(self) -> None:
    result = self._run_langgraph()
    self.app.call_from_thread(self.post_message, self.DataReady(result))
```

- **Reference**: https://textual.textualize.io/guide/workers/

### Thread Safety: `call_from_thread`

When code runs in a background thread (e.g. a `@work(thread=True)` worker or a raw `threading.Thread`), it must not touch the widget tree directly. Use `app.call_from_thread()` to schedule UI updates safely:

```python
import threading

def _background(self) -> None:
    result = self._blocking_call()
    self.app.call_from_thread(self.post_message, self.DataReady(result))

# Or call any callable
self.app.call_from_thread(self.refresh)
self.app.call_from_thread(setattr, self, "status", "done")
```

- **Reference**: https://textual.textualize.io/guide/workers/#thread-workers

### Custom Messages and `post_message`

The idiomatic way to communicate between widgets (and up the DOM) is custom message classes:

```python
from textual.message import Message

class MyWidget(Widget):
    class DataReady(Message):
        def __init__(self, data: dict) -> None:
            super().__init__()
            self.data = data

    def _on_work_done(self, result: dict) -> None:
        self.post_message(self.DataReady(result))

# Parent handles it
class ParentWidget(Widget):
    def on_my_widget_data_ready(self, event: MyWidget.DataReady) -> None:
        self.update(event.data)
```

Messages bubble up the DOM by default. Set `BUBBLE = False` on the class to stop propagation.

- **Reference**: https://textual.textualize.io/guide/events/#custom-messages

## Built-in Widgets

Textual provides many ready-to-use widgets:

| Widget | Description | Reference |
|--------|-------------|------------|
| Button | Clickable button | https://textual.textualize.io/widgets/button/ |
| Input | Text input field | https://textual.textualize.io/widgets/input/ |
| Label | Static text display | https://textual.textualize.io/widgets/label/ |
| Static | Generic content | https://textual.textualize.io/widgets/static/ |
| DataTable | Tabular data | https://textual.textualize.io/widgets/data_table/ |
| Tree | Hierarchical data | https://textual.textualize.io/widgets/tree/ |
| RichLog | Rich text logging | https://textual.textualize.io/widgets/rich_log/ |
| ListView | Scrollable list | https://textual.textualize.io/widgets/list_view/ |
| Tabs | Tabbed interface | https://textual.textualize.io/widgets/tabs/ |
| TextArea | Multi-line editor | https://textual.textualize.io/widgets/text_area/ |

**Full widget gallery**: https://textual.textualize.io/widget_gallery/

## Testing

Textual provides a `Pilot` class for headless testing:

```python
import pytest
from textual.app import App

async def test_app():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.click("#my-button")
        await pilot.press("a")
        assert app.screen.styles.background == Color.parse("red")
```

**Key Methods:**
- `run_test()` - Run app in headless mode
- `pilot.press("key")` - Simulate key press
- `pilot.click("#selector")` - Simulate mouse click
- `pilot.pause()` - Wait for pending messages

**Reference**: https://textual.textualize.io/guide/testing/

### Snapshot Testing

Install `pytest-textual-snapshot` for visual regression testing:

```bash
pip install pytest-textual-snapshot
```

```python
def test_app_snapshot(snap_compare):
    assert snap_compare("path/to/app.py")
```

- **Plugin**: https://github.com/Textualize/pytest-textual-snapshot

## Textual-Serve Integration

`textual-serve` runs a Textual app on your machine and exposes it in the browser over websocket:

```bash
pip install textual-serve
```

```python
from textual_serve.server import Server

server = Server("python -m textual", host="localhost", port=8000)
server.serve()
```

**Common use:**
- Local browser access for a Textual app
- Self-hosted browser demo environment
- Same app process, terminal or browser

**Reference**: https://github.com/Textualize/textual-serve

## API Reference

| Module | Description | Reference |
|--------|-------------|------------|
| `textual.app` | App class | https://textual.textualize.io/api/app/ |
| `textual.widget` | Widget base class | https://textual.textualize.io/api/widget/ |
| `textual.screen` | Screen class | https://textual.textualize.io/api/screen/ |
| `textual.reactive` | Reactive attributes | https://textual.textualize.io/api/reactive/ |
| `textual.pilot` | Testing pilot | https://textual.textualize.io/api/pilot/ |
| `textual.containers` | Layout containers | https://textual.textualize.io/api/containers/ |
| `textual.binding` | Key bindings | https://textual.textualize.io/api/binding/ |
| `textual.on` | Event decorator | https://textual.textualize.io/api/on/ |
| `textual.work` | Worker decorator | https://textual.textualize.io/api/work/ |

## Style Reference

### Colors

- Use `$primary`, `$secondary`, `$surface`, `$panel`, etc.
- Or explicit: `"red"`, `"#FF0000"`, `"rgb(255,0,0)"`

### Layout

- `layout: vertical` - Stack vertically (default)
- `layout: horizontal` - Stack horizontally
- `layout: grid` - Grid layout

### Dimensions

- `width: 1fr`, `height: auto`
- `width: 50%`, `height: 10`
- `min-height: 5`, `max-width: 80`

### Borders

- `border: solid $primary`
- `border-bottom: heavy red`

### Display

- `display: none` / `display: block`
- `visibility: hidden` / `visibility: visible`

**Full CSS reference**: https://textual.textualize.io/guide/styles/

## Debugging

Use the devtools:

```bash
textual run --dev path/to/app.py
```

- `Ctrl+Shift+F` - Toggle file finder
- `Ctrl+Shift+S` - Toggle screen inspector

**Reference**: https://textual.textualize.io/guide/devtools/

## Project Structure Recommendation

```
src/review_ui/
├── __init__.py
├── app.py              # Main App class
├── bus.py              # Data layer (MatchBus)
└── screens/
    ├── __init__.py
    ├── review_screen.py    # Main review screen
    └── explorer_screen.py  # Job browser
```

## See Also

- [Getting Started](https://textual.textualize.io/getting_started/)
- [Tutorial](https://textual.textualize.io/tutorial/)
- [FAQ](https://textual.textualize.io/FAQ/)
- [Roadmap](https://textual.textualize.io/roadmap/)
