# Ariadne Translators

Date: 2026-04-05
Status: design-only

## Purpose

Define how Ariadne common-language steps compile into motor-specific execution
formats. Each motor has one translator. Translation is deterministic — no LLM,
no runtime inference, no network calls. Given the same AriadnePath and context,
the translator always produces the same output.

## Translator contract

Every translator implements the same interface:

```python
class AriadneTranslator(ABC):
    @abstractmethod
    def can_translate(self, path: AriadnePath) -> bool:
        """Check if this translator can handle the path.

        Returns False if required AriadneTarget fields are missing for this motor.
        For example, the Crawl4AI translator returns False if no step has a css target.
        """

    @abstractmethod
    def translate(self, path: AriadnePath, context: dict) -> MotorPlan:
        """Compile an AriadnePath into motor-specific execution instructions.

        Resolves {{placeholders}} from context. Raises TranslationError if
        a step cannot be compiled.
        """
```

The output type (`MotorPlan`) is motor-specific. The translator is the only place
where motor-specific knowledge exists on the output side.

## Translator per motor

### Crawl4AI translator — a compiler

The Crawl4AI translator is the most complex because Crawl4AI's execution model
(batch C4A-Script strings) differs fundamentally from Ariadne's step model.

**Input:** list of `AriadneStep`
**Output:** list of `CrawlPhase` (each is one `arun()` call with a C4A-Script)

**Compilation rules:**

Steps are grouped into phases. Phase boundaries correspond to separate `arun()` calls
(currently: navigate/open, fill, submit are three separate calls in `smart_adapter.py`).

| AriadneAction intent | C4A-Script construct |
|---|---|
| `click` | `CLICK "{css_selector}"` or `CLICK_TEXT "{text}"` |
| `fill` | `TYPE "{css_selector}" "{value}"` |
| `fill_react_controlled` | `EXECUTE_JS "const el = document.querySelector('{css}'); ..."` |
| `select` | `SELECT "{css_selector}" "{value}"` |
| `upload` | Cannot be expressed in C4A-Script — compiled as a Playwright hook |
| `wait` | `WAIT_FOR "css:{selector}"` or `WAIT_FOR_TEXT "{text}"` |

**Fallback compilation:** `AriadneAction.fallback` compiles to `IF/ELSE` in C4A-Script:

```
IF_ELEMENT "{primary_css}"
  CLICK "{primary_css}"
ELSE
  CLICK "{fallback_css}"
```

**Observe compilation:** `AriadneObserve.expected_elements` compile to `WAIT_FOR`
guards at the start of each phase.

**Target field used:** `AriadneTarget.css` (primary). Falls back to `AriadneTarget.text`
for `CLICK_TEXT`/`WAIT_FOR_TEXT` constructs. If neither is available, raises
`TranslationError`.

**Upload handling:** since file uploads have no C4A-Script equivalent, they compile
to a `before_retrieve_html` hook using Playwright's `page.set_input_files()`.
This is the same pattern as the current `ApplyAdapter._build_file_upload_hook()`.

### BrowserOS CLI translator — a mapper

The BrowserOS CLI translator is straightforward because BrowserOS's execution model
(individual tool calls in a loop) maps 1:1 to Ariadne steps.

**Input:** list of `AriadneStep`
**Output:** list of `BrowserOSStepPlan` (each is a sequence of MCP tool calls)

| AriadneAction intent | BrowserOS MCP tool call |
|---|---|
| `click` | `click(page, element_id)` — element resolved from snapshot via text match |
| `fill` | `fill(page, element_id, value)` |
| `fill_react_controlled` | `evaluate_script(page, react_setter_script)` |
| `select` | `select_option(page, element_id, value)` |
| `upload` | `upload_file(page, element_id, file_path)` |
| `press_key` | `press_key(page, key)` |
| `scroll` | `scroll(page, ...)` |
| `wait` | poll `take_snapshot` until expected elements appear |

**Observe translation:** `AriadneObserve.expected_elements` → `take_snapshot()` +
assert expected elements present via text matching (same as current
`BrowserOSPlaybookExecutor._assert_expected_elements()`).

**Target field used:** `AriadneTarget.text` (primary, fuzzy snapshot matching).
Falls back to `AriadneTarget.css` (via `search_dom` or Playwright selector).
If neither is available, raises `TranslationError`.

**Fallback translation:** `AriadneAction.fallback` → try primary target resolution;
if `TargetNotFound`, execute fallback action instead (same as current
`BrowserOSPlaybookExecutor._execute_action()` fallback logic).

### Vision translator — a resolver, not an executor

The vision translator does not produce execution instructions. It resolves
`AriadneTarget` fields into screen coordinates that other motors consume.

**Input:** `AriadneTarget` with `image_template` or `ocr_text`
**Output:** `VisionMatch` (x, y, width, height, confidence)

| AriadneTarget field | Vision operation |
|---|---|
| `image_template` | OpenCV `matchTemplate` against screenshot |
| `ocr_text` | OCR scan of screenshot, find text region |
| `region` | Restrict search to bounding box |

The vision translator is called by other translators (or the orchestrator) when
their primary target fields are missing but vision fields are available.

### OS Native translator — a coordinate consumer

The OS native translator compiles Ariadne intents into physical input events.

**Input:** `AriadneAction` + resolved coordinates (from vision or other source)
**Output:** OS-level input commands

| AriadneAction intent | OS native command |
|---|---|
| `click` | `native_click(x, y)` |
| `fill` | `native_click(x, y)` then `native_type(value)` |
| `select` | `native_click(x, y)` then `native_click(option_x, option_y)` |
| `upload` | OS file dialog interaction (complex, TBD) |
| `press_key` | `native_keypress(key)` |

**Target field used:** requires coordinates, typically from the vision translator.
If `AriadneTarget` has no vision fields and no coordinates, raises `TranslationError`.

### Human "translator" — a presentation layer

The human motor doesn't have a translator in the compilation sense. Instead,
the AriadnePath is presented to the human as instructions:

- Step name and description displayed
- Expected elements listed (so the human can verify the page)
- Actions described in natural language ("click the Submit button", "fill the
  First Name field with your name")
- `human_required` steps highlighted
- `dry_run_stop` steps flagged as checkpoints

This is only relevant for guided human sessions (human following an existing
path for verification). For free exploration (recording), no translator is needed.

## Translation error handling

All translators raise errors from the Ariadne error taxonomy (see `error_taxonomy.md`):

- `TranslationError` — a step cannot be compiled to the motor's format
  (missing required target field, unsupported intent, etc.)
- Translators never raise motor-specific errors. Motor execution may raise
  `TargetNotFound`, `ObservationFailed`, etc., but those happen at execution
  time, not translation time.

## Translator selection

When replaying a path, the system must choose which translator to use.
Selection logic:

1. Operator specifies motor explicitly (`--backend crawl4ai`)
2. If not specified, check `AriadnePath` target field coverage:
   - All steps have `css` → Crawl4AI is viable
   - All steps have `text` → BrowserOS CLI is viable
   - Steps have `image_template` only → Vision + OS Native required
3. If multiple motors are viable, prefer the most deterministic:
   Crawl4AI > BrowserOS CLI > OS Native + Vision

## Open questions

1. Should translators be stateless (pure function: path + context → plan) or
   stateful (aware of page state during translation)? Stateless is simpler
   and more testable. Stateful enables runtime target resolution.
2. Should the Crawl4AI translator's phase boundaries be configurable or
   hard-coded? Current code uses 3 phases (navigate, fill, submit) but
   different portals may need different groupings.
3. Can a single path be translated to multiple motors simultaneously for
   hybrid execution? (e.g., Crawl4AI for form fill, vision for verification)
4. Should translator output be cacheable? If the same path + context always
   produces the same motor plan, caching avoids re-compilation.
