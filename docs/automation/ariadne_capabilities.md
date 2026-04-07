# Ariadne Capability Registry

This document maps high-level **Ariadne Intents** to the low-level capabilities of the integrated motors (**Crawl4AI** and **BrowserOS**). It serves as the source of truth for the compiler and replayer implementations to ensure we don't "blind" ourselves to motor-specific superpowers.

## 1. Interaction Capability Map

| Ariadne Intent | Crawl4AI (C4A-Script) | BrowserOS (MCP Tool) | Notes |
| :--- | :--- | :--- | :--- |
| **`CLICK`** | `CLICK <sel>` | `click` | BrowserOS supports fuzzy text clicking. |
| **`FILL`** | `SET <sel> "<val>"` | `fill` | Crawl4AI `SET` is fast; `TYPE` is slower/human-like. |
| **`FILL_REACT`** | (Custom JS) | `evaluate_script_react` | Special handling for React controlled components. |
| **`SELECT`** | `SELECT <sel> "<val>"` | `select_option` | Dropdown/Combobox selection. |
| **`UPLOAD`** | `UPLOAD <sel> "<path>"` | `upload_file` | Implemented via `before_retrieve_html` hook for reliability. |
| **`PRESS_KEY`** | `PRESS <key>` | `press_key` | Supports Tab, Enter, Escape, etc. |
| **`SCROLL`** | `SCROLL <dir> <amt>` | `scroll_page` | Crawl4AI supports specific pixel amounts. |
| **`WAIT`** | `WAIT <sel> <timeout>` | (Implicit/Snapshot) | BrowserOS usually waits for snapshot stability. |
| **`NAVIGATE`** | `GO <url>` | `navigate_page` | Direct URL navigation. |
| **`RELOAD`** | `RELOAD` | `navigate_page` (action: reload) | Page refresh. |
| **`BACK`** | `BACK` | `navigate_page` (action: back) | Browser history navigation. |

---

## 2. Observation & Guard Capability Map

These capabilities are used in `AriadneObserve` and `AriadneState` predicates.

| Capability | Crawl4AI | BrowserOS | Notes |
| :--- | :--- | :--- | :--- |
| **CSS Presence** | `IF (EXISTS <sel>)` | `search_dom` | High precision. |
| **Text Presence** | `WAIT "<text>"` | `take_snapshot` | BrowserOS is superior here (fuzzy matching). |
| **Negative Guard** | `IF (NOT EXISTS <sel>)` | (Logic-based) | Used to detect dead ends or loading states. |
| **Visual Match** | (Not supported) | `take_screenshot` | Vision motor will eventually own this. |

---

## 3. Motor Superpowers (Ariadne Metadata)

Features that are unique to one motor but can be triggered via `AriadneAction.metadata`.

### Crawl4AI Superpowers
*   **`js_code`**: Execute raw JavaScript using `EVAL \ <code> \`.
*   **`wait_for_network`**: Wait for idle network connections before proceeding.
*   **`extraction_schema`**: Define a Pydantic schema for structured data extraction during an apply flow.

### BrowserOS Superpowers
*   **`fuzzy_threshold`**: Adjust the sensitivity of text matching.
*   **`enhanced_snapshot`**: Capture structural page metadata optimized for LLM consumption.
*   **`external_integration`**: Direct triggers for Slack, Gmail, or Notion (Zero-Config Auth).

---

## 4. References
*   [Crawl4AI C4A-Script Documentation](https://docs.crawl4ai.com/core/c4a-script/)
*   [BrowserOS MCP Tools Overview](https://docs.browseros.com/mcp/tools)
