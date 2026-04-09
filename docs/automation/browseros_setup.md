# BrowserOS Setup

BrowserOS provides the authenticated browser session needed for LinkedIn and XING apply flows. This document covers setup, session management, and troubleshooting.

## Starting BrowserOS

```bash
# Launch the BrowserOS runtime
/home/jp/BrowserOS.AppImage --no-sandbox

# Verify the stable local front door
curl http://127.0.0.1:9000/mcp
```

BrowserOS is an external runtime. This repository talks to it through the
stable local front door at `http://127.0.0.1:9000` by default.

- MCP endpoint: `http://127.0.0.1:9000/mcp`
- Agent chat endpoint: `http://127.0.0.1:9000/chat` (optional for scrape rescue)
- Override base URL with `BROWSEROS_BASE_URL`

The deeper BrowserOS reference index lives at
`docs/reference/external_libs/browseros/readme.txt`.

## Extraction Fallback Configuration

Scrape runs use `src/automation/motors/crawl4ai/scrape_engine.py` as the
definition point for extraction fallback order.

Configure fallback order with `AUTOMATION_EXTRACTION_FALLBACKS`:

```bash
# BrowserOS first, then Gemini rescue
export AUTOMATION_EXTRACTION_FALLBACKS="browseros,llm"

# BrowserOS only
export AUTOMATION_EXTRACTION_FALLBACKS="browseros"
```

Notes:
- `browseros` uses BrowserOS MCP rescue and does not require a Google key.
- `llm` uses Crawl4AI `LLMExtractionStrategy` and requires `GOOGLE_API_KEY`.

## Setting Up an Authenticated Session

BrowserOS uses `--setup-session` to capture a login session for a portal:

```bash
# Setup session for XING
python -m src.automation.main apply \
  --source xing \
  --backend browseros \
  --setup-session

# Setup session for LinkedIn
python -m src.automation.main apply \
  --source linkedin \
  --backend browseros \
  --setup-session
```

This opens an interactive browser where you log in normally. On success, the session is persisted to `~/.config/browseros/sessions/<portal>.json`.

The canonical live apply validation scope is defined in
`docs/automation/live_apply_validation_matrix.md`.

## Running a Dry-Run Apply

```bash
# XING dry-run (requires authenticated session)
python -m src.automation.main apply \
  --source xing \
  --backend browseros \
  --job-id <job-id> \
  --cv /path/to/cv.pdf \
  --dry-run

# LinkedIn dry-run
python -m src.automation.main apply \
  --source linkedin \
  --backend browseros \
  --job-id <job-id> \
  --cv /path/to/cv.pdf \
  --dry-run
```

Use `docs/automation/live_apply_validation_matrix.md` to decide whether a
portal/backend/mode combination is in scope before running live validation.

## Session Persistence Location

Sessions are stored at:
- Linux/macOS: `~/.config/browseros/sessions/`
- Windows: `%APPDATA%/browseros/sessions/`

## Switching Sessions

To use a different account or refresh a session:

```bash
# Remove existing session and re-authenticate
rm ~/.config/browseros/sessions/xing.json
python -m src.automation.main apply --source xing --backend browseros --setup-session
```

## Troubleshooting

### `Connection refused` on `127.0.0.1:9000`
BrowserOS runtime is not running. Start it with:

```bash
/home/jp/BrowserOS.AppImage --no-sandbox
```

If BrowserOS is running on a different local front door, set:

```bash
export BROWSEROS_BASE_URL="http://127.0.0.1:<port>"
```

### Session expired (login required)
Remove the session file and re-run `--setup-session`.

### `net::ERR_NETWORK_CHANGED`
Transient network error. Retry the apply command — up to 3 retries are implemented in the scrape engine.

## Test Fixtures

Use `tests/fixtures/test-cv.pdf` for testing:
```bash
python -m src.automation.main apply \
  --source xing \
  --backend browseros \
  --job-id <test-id> \
  --cv tests/fixtures/test-cv.pdf \
  --dry-run
```
