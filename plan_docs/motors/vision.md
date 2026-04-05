# Vision Motor — Placeholder

Date: 2026-04-05
Status: design-only, no code exists

## What this motor should do

Look at the screen — detect elements, read text, verify visual state. This is the
"eyes" motor: it produces observations and target coordinates but never acts on
the page.

Use cases:

- Locate a button/field by matching an image template (OpenCV template matching)
- Read text from a region via OCR (for pages that render text as images or canvas)
- Verify visual state ("is the modal open?", "did the page change?") via image diff
- Provide coordinates to OS native tools or other motors for interaction
- Visual assertion in any backend's replay loop ("does the page look like step 3?")

## Relationship to other motors

- **Vision looks, OS native acts.** Vision produces bounding boxes and coordinates;
  OS native (or any other motor) consumes them. Neither depends on the other.
- **Standalone observation.** Vision can run as a verification step in any replay
  loop (Crawl4AI, BrowserOS, OS native) without triggering actions.
- **Ariadne target resolution.** When an `AriadneTarget` has `image_template` or
  `ocr_text` fields but no `css` or `text`, vision is the resolver.

## What needs to be documented before implementation

### Observation primitives

What atomic observations does this motor expose?

- [ ] `match_template(image_path, region?) → bounding_box | None` — find an image template on screen
- [ ] `match_template_multi(image_path, region?) → list[bounding_box]` — find all instances
- [ ] `ocr_region(region) → str` — extract text from a screen region
- [ ] `ocr_find(text, region?) → bounding_box | None` — find text on screen and return its location
- [ ] `diff_region(region, reference_image) → float` — similarity score between current screen and reference
- [ ] `wait_for_template(image_path, timeout, region?) → bounding_box` — poll until template appears
- [ ] `wait_for_text(text, timeout, region?) → bounding_box` — poll until OCR text appears
- [ ] `screenshot(region?) → image` — capture screen or region for downstream processing

### Screen capture source

Where does the vision motor get its input image?

- [ ] OS-level screen capture (full screen or region)
- [ ] BrowserOS `take_screenshot` / `save_screenshot` output
- [ ] Crawl4AI screenshot output
- [ ] Arbitrary image file (for offline/test verification)

Define which sources are supported and whether the motor captures its own
screenshots or always receives them.

### Template management

- [ ] Where do image templates live? (`ariadne/traces/`? portal-local? motor-local?)
- [ ] How are templates versioned? (portal redesigns invalidate templates)
- [ ] What resolution/scale are templates captured at? How to handle DPI variation?
- [ ] Should templates be cropped tightly or include surrounding context?
- [ ] Template naming convention (e.g., `linkedin.easy_apply.step5.submit_button.png`)

### OCR configuration

- [ ] Which OCR engine? (Tesseract, EasyOCR, PaddleOCR?)
- [ ] Language support (at minimum: English, German, Spanish)
- [ ] Confidence threshold for text matching
- [ ] How to handle partial matches ("Enviar solicitud" vs "Enviar solicit...")

### Matching parameters

- [ ] Template matching threshold (OpenCV `matchTemplate` confidence cutoff)
- [ ] Scale invariance — does the motor handle templates at different scales?
- [ ] Rotation invariance — needed or out of scope?
- [ ] Region of interest — can the caller restrict matching to a subregion?

### Output contract

What does the vision motor return to callers?

```python
@dataclass
class VisionMatch:
    x: int              # center x of bounding box (screen coordinates)
    y: int              # center y of bounding box (screen coordinates)
    width: int          # bounding box width
    height: int         # bounding box height
    confidence: float   # match confidence (0.0–1.0)
    method: str         # "template" | "ocr" | "diff"
    source_hint: str    # what was searched for (template path or OCR text)
```

This is what OS native tools (or any motor) consume as coordinates.

### Backend contract for Ariadne translation

What does the translator need to compile from common language?

- `AriadneTarget` with `image_template` → `vision.match_template(path)` → coordinates
- `AriadneTarget` with `ocr_text` → `vision.ocr_find(text)` → coordinates
- `AriadneAction` intent `observe` with visual assertion → `vision.diff_region()` or `vision.ocr_region()`
- Vision never executes `click`, `fill`, `upload`, etc. — it returns coordinates and
  the orchestrator routes to the appropriate action motor.

### Error taxonomy mapping

- `TargetNotFound` — template/OCR text not found on screen within timeout
- `ObservationFailed` — screenshot capture failed or image processing error
- `PortalStructureChanged` — multiple consecutive observation failures suggest visual drift

### Observation-only guarantee

How do we enforce that vision never acts?

- [ ] Motor interface exposes only observation methods (no click, fill, type)
- [ ] Ariadne translator for vision only handles `observe` intents and target resolution
- [ ] If an `AriadneAction` with `image_template` target needs a click, the orchestrator
      calls vision for resolution then routes the click to another motor

## Implementation dependencies

- Ariadne common-language models with `AriadneTarget.image_template`, `ocr_text`, `region` fields
- Ariadne error taxonomy
- Screen capture source decision (own capture vs receive from other motors)
- Template storage location decision
- At least one consumer ready to use vision output (OS native tools or BrowserOS coordinate click)

## Open questions

1. Should the vision motor own screen capture or always receive images from the
   caller? Owning capture is simpler but couples it to the display environment.
2. Is OpenCV `matchTemplate` sufficient, or do we need feature-based matching
   (SIFT/ORB) for scale/rotation invariance?
3. Should OCR run on every observation step or only when explicitly requested?
   (Performance vs completeness tradeoff.)
4. How do we handle dynamic content (animations, loading spinners) that cause
   template matching to flicker?
5. Should visual assertions ("page looks like reference") be a first-class
   Ariadne step type or a motor-level convenience?
6. What is the latency budget? Template matching on a full 1080p screenshot
   takes ~10-50ms; OCR takes ~200-500ms. Is this acceptable in a replay loop?
