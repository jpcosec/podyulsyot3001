# Vision Motor Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts for the Vision motor. Vision resolves AriadneTargets into screen
coordinates and performs visual assertions. It never acts — it only looks.
Other motors and translators call vision when they need coordinate resolution
or visual verification.

## Resolution contracts

### VisionQuery

Input to the vision motor: "find this on screen."

```python
class VisionQuery(BaseModel):
    query_type: Literal["template_match", "ocr_find", "region_ocr", "diff"]
    image_template: str | None = None    # path to template image (for template_match)
    ocr_text: str | None = None          # text to find (for ocr_find)
    region: VisionRegion | None = None   # restrict search area
    reference_image: str | None = None   # path to reference (for diff)
    confidence_threshold: float = 0.8    # minimum match confidence
    timeout_ms: int | None = None        # poll until found or timeout
```

### VisionRegion

Bounding box to restrict search or describe a result location.

```python
class VisionRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int
```

### VisionMatch

Output from the vision motor: "found it here."

```python
class VisionMatch(BaseModel):
    x: int                      # center x of bounding box (screen coordinates)
    y: int                      # center y of bounding box (screen coordinates)
    width: int
    height: int
    confidence: float           # 0.0–1.0
    method: Literal["template", "ocr", "diff"]
    source_hint: str            # what was searched for (template path or text)
```

This is what OS native tools (or any motor) consume as coordinates.

### VisionDiffResult

Output from a visual comparison.

```python
class VisionDiffResult(BaseModel):
    similarity: float           # 0.0–1.0 (1.0 = identical)
    method: Literal["diff"]
    region: VisionRegion
    reference_image: str
```

## Screenshot contracts

### VisionScreenshot

Input image for vision operations. Can come from any source.

```python
class VisionScreenshot(BaseModel):
    source: Literal["os_capture", "browseros", "crawl4ai", "file"]
    image_path: str | None = None    # path to image file
    image_data: bytes | None = None  # raw image bytes (alternative to path)
    captured_at: str | None = None
    region: VisionRegion | None = None  # if this is a cropped region
```

## Template contracts

### VisionTemplate

Metadata for a stored image template.

```python
class VisionTemplate(BaseModel):
    template_id: str             # e.g. "linkedin.easy_apply.step5.submit_button"
    image_path: str              # relative path to template image
    source: str                  # portal name
    description: str | None = None
    captured_at: str | None = None
    capture_resolution: tuple[int, int] | None = None  # width x height of original screen
```

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `VisionQuery` | (no equivalent) | — |
| `VisionRegion` | (no equivalent — `region: dict` in AriadneTarget) | — |
| `VisionMatch` | (no equivalent) | — |
| `VisionScreenshot` | (no equivalent) | — |
| `VisionTemplate` | (no equivalent) | — |

Everything here is new — the vision motor has no code today.
