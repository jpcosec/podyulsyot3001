# UI Improvements & Data Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broken icon rendering, add a JSON/MD data explorer at `/explorer`, fix console errors, and clean up the portfolio page.

**Architecture:** Four independent tasks that can be parallelized. The data explorer requires a new backend endpoint (`GET /api/v1/explorer/browse`) that returns directory listings and file contents from `data/jobs/`, plus a new React page. Icons are a one-line HTML fix. Console errors need deduplication in the view payloads.

**Tech Stack:** React 18 + TypeScript, FastAPI, React Router, existing Terran Command CSS theme

---

## File Structure

```
Backend (new):
  src/interfaces/api/routers/explorer.py     # New router for browsing data/jobs/

Frontend (new):
  apps/review-workbench/src/pages/DataExplorerPage.tsx  # Tree + preview page

Frontend (modify):
  apps/review-workbench/index.html            # Add Material Symbols font link
  apps/review-workbench/src/App.tsx            # Add /explorer route
  apps/review-workbench/src/api/client.ts      # Add explorer API functions
  apps/review-workbench/src/pages/PortfolioPage.tsx  # Restructure layout
Backend (modify):
  src/interfaces/api/app.py                   # Mount explorer router
```

---

### Task 1: Fix Material Symbols icon font

**Files:**
- Modify: `apps/review-workbench/index.html`

- [ ] **Step 1: Add the Google Fonts link for Material Symbols Outlined**

In `apps/review-workbench/index.html`, add inside `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
```

- [ ] **Step 2: Verify icons render in browser**

Open http://127.0.0.1:4174/jobs/tu_berlin/202362/deployment in browser.
Expected: `check_circle`, `radio_button_unchecked`, `send`, `pending` render as actual icons instead of text.

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/index.html
git commit -m "fix(ui): add Material Symbols font import for icon rendering"
```

---

### Task 2: Data Explorer — Backend endpoint

**Files:**
- Create: `src/interfaces/api/routers/explorer.py`
- Modify: `src/interfaces/api/app.py`

- [ ] **Step 1: Create the explorer router**

Create `src/interfaces/api/routers/explorer.py`:

```python
from __future__ import annotations

import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.interfaces.api.config import load_settings

router = APIRouter(prefix="/api/v1/explorer", tags=["explorer"])

MAX_FILE_SIZE = 512 * 1024  # 512 KB preview limit
PREVIEWABLE_EXTENSIONS = {".json", ".md", ".txt", ".yaml", ".yml", ".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg"}


@router.get("/browse")
def browse(path: str = Query("", description="Relative path within data root")) -> dict:
    """List directory contents or return file preview."""
    settings = load_settings()
    data_root = Path(settings.data_root).resolve()
    target = (data_root / path).resolve()

    # Security: prevent path traversal (is_relative_to is safe against sibling dirs)
    if not target.is_relative_to(data_root):
        raise HTTPException(status_code=403, detail="path traversal not allowed")

    if not target.exists():
        raise HTTPException(status_code=404, detail="path not found")

    if target.is_file():
        return _read_file(target, data_root)

    entries = []
    for child in sorted(target.iterdir()):
        rel = child.relative_to(data_root)
        entry = {
            "name": child.name,
            "path": str(rel),
            "is_dir": child.is_dir(),
        }
        if child.is_file():
            entry["size_bytes"] = child.stat().st_size
            entry["extension"] = child.suffix.lower()
        if child.is_dir():
            try:
                entry["child_count"] = sum(1 for _ in child.iterdir())
            except PermissionError:
                entry["child_count"] = 0
        entries.append(entry)

    # Sort: directories first, then files
    entries.sort(key=lambda e: (not e["is_dir"], e["name"]))

    return {
        "path": path or ".",
        "is_dir": True,
        "entries": entries,
    }


def _read_file(target: Path, data_root: Path) -> dict:
    rel = str(target.relative_to(data_root))
    ext = target.suffix.lower()
    size = target.stat().st_size

    result: dict = {
        "path": rel,
        "is_dir": False,
        "name": target.name,
        "extension": ext,
        "size_bytes": size,
    }

    if ext in IMAGE_EXTENSIONS and size <= MAX_FILE_SIZE:
        raw = target.read_bytes()
        mime = "image/png" if ext == ".png" else "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/svg+xml" if ext == ".svg" else "image/gif"
        result["content_type"] = "image"
        result["content"] = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
        return result

    if ext not in PREVIEWABLE_EXTENSIONS:
        result["content_type"] = "binary"
        result["content"] = None
        return result

    if size > MAX_FILE_SIZE:
        result["content_type"] = "too_large"
        result["content"] = None
        return result

    text = target.read_text(errors="replace")
    result["content_type"] = "text"
    result["content"] = text
    return result
```

- [ ] **Step 2: Mount the explorer router in the FastAPI app**

In `src/interfaces/api/app.py`, add:

```python
from src.interfaces.api.routers.explorer import router as explorer_router
```

And in `create_app()`, add:

```python
app.include_router(explorer_router)
```

- [ ] **Step 3: Test the endpoint manually**

```bash
curl -s http://127.0.0.1:8010/api/v1/explorer/browse | python -m json.tool | head -30
curl -s "http://127.0.0.1:8010/api/v1/explorer/browse?path=tu_berlin" | python -m json.tool | head -30
```

Expected: JSON with `entries` array listing directories/files.

- [ ] **Step 4: Commit**

```bash
git add src/interfaces/api/routers/explorer.py src/interfaces/api/app.py
git commit -m "feat(api): add data explorer browse endpoint"
```

---

### Task 3: Data Explorer — Frontend page

**Files:**
- Create: `apps/review-workbench/src/pages/DataExplorerPage.tsx`
- Modify: `apps/review-workbench/src/App.tsx`
- Modify: `apps/review-workbench/src/api/client.ts`
- Modify: `apps/review-workbench/src/pages/PortfolioPage.tsx`

- [ ] **Step 1: Add the API client function**

In `apps/review-workbench/src/api/client.ts`, add the import for `ExplorerPayload` at the top with the other type imports, then add the function:

```typescript
export async function browseExplorer(path: string = ""): Promise<ExplorerPayload> {
  const params = path ? `?path=${encodeURIComponent(path)}` : "";
  const res = await fetch(`${API_BASE}/api/v1/explorer/browse${params}`);
  if (!res.ok) throw new Error(`Explorer browse failed: ${res.status}`);
  return res.json();
}
```

- [ ] **Step 2: Add the TypeScript types**

In `apps/review-workbench/src/types/models.ts`, add:

```typescript
export interface ExplorerEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size_bytes?: number;
  extension?: string;
  child_count?: number;
}

export interface ExplorerPayload {
  path: string;
  is_dir: boolean;
  entries?: ExplorerEntry[];
  name?: string;
  extension?: string;
  size_bytes?: number;
  content_type?: "text" | "image" | "binary" | "too_large";
  content?: string | null;
}
```

- [ ] **Step 3: Create the DataExplorerPage component**

Create `apps/review-workbench/src/pages/DataExplorerPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { browseExplorer } from "../api/client";
import type { ExplorerPayload } from "../types/models";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function BreadcrumbNav({ currentPath }: { currentPath: string }): JSX.Element {
  const parts = currentPath.split("/").filter(Boolean);
  const crumbs = [{ label: "data/jobs", path: "" }];
  let accumulated = "";
  for (const part of parts) {
    accumulated = accumulated ? `${accumulated}/${part}` : part;
    crumbs.push({ label: part, path: accumulated });
  }
  return (
    <div className="breadcrumbs">
      {crumbs.map((crumb, i) => (
        <span key={crumb.path}>
          {i > 0 && <span>/</span>}
          {i < crumbs.length - 1 ? (
            <Link to={`/explorer?path=${encodeURIComponent(crumb.path)}`}>{crumb.label}</Link>
          ) : (
            <span>{crumb.label}</span>
          )}
        </span>
      ))}
    </div>
  );
}

function FilePreview({ data }: { data: ExplorerPayload }): JSX.Element {
  if (data.content_type === "image" && data.content) {
    return <img src={data.content} alt={data.name} style={{ maxWidth: "100%", borderRadius: 4 }} />;
  }
  if (data.content_type === "too_large") {
    return <p className="text-dim">File too large to preview ({formatSize(data.size_bytes ?? 0)})</p>;
  }
  if (data.content_type === "binary") {
    return <p className="text-dim">Binary file — no preview available</p>;
  }
  const isJson = data.extension === ".json";
  let displayContent = data.content ?? "";
  if (isJson) {
    try {
      displayContent = JSON.stringify(JSON.parse(displayContent), null, 2);
    } catch { /* keep raw */ }
  }
  return (
    <pre className="explorer-preview">{displayContent}</pre>
  );
}

export function DataExplorerPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const currentPath = searchParams.get("path") ?? "";
  const [data, setData] = useState<ExplorerPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    setError("");
    browseExplorer(currentPath)
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [currentPath]);

  return (
    <section className="panel">
      <BreadcrumbNav currentPath={currentPath} />
      <h1>Data Explorer</h1>
      <p className="text-dim">Browse local artifacts in data/jobs/</p>

      {error && <p className="error">{error}</p>}

      {data?.is_dir && data.entries && (
        <div className="explorer-list">
          {data.entries.map((entry) => (
            <Link
              key={entry.path}
              to={`/explorer?path=${encodeURIComponent(entry.path)}`}
              className="explorer-entry"
            >
              <span className="material-symbols-outlined">
                {entry.is_dir ? "folder" : "description"}
              </span>
              <span className="explorer-entry-name">{entry.name}</span>
              {!entry.is_dir && entry.size_bytes != null && (
                <span className="explorer-entry-meta">{formatSize(entry.size_bytes)}</span>
              )}
              {entry.is_dir && entry.child_count != null && (
                <span className="explorer-entry-meta">{entry.child_count} items</span>
              )}
            </Link>
          ))}
          {data.entries.length === 0 && <p className="text-dim">Empty directory</p>}
        </div>
      )}

      {data && !data.is_dir && (
        <div className="explorer-file-view">
          <div className="explorer-file-header">
            <strong>{data.name}</strong>
            {data.size_bytes != null && <span className="text-dim">{formatSize(data.size_bytes)}</span>}
          </div>
          <FilePreview data={data} />
        </div>
      )}

      {!data && !error && <p>Loading...</p>}
    </section>
  );
}
```

- [ ] **Step 4: Add the route in App.tsx**

In `apps/review-workbench/src/App.tsx`, add import and route:

```tsx
import { DataExplorerPage } from "./pages/DataExplorerPage";
```

Add route before the sandbox routes:

```tsx
<Route path="/explorer" element={<DataExplorerPage />} />
```

- [ ] **Step 5: Add CSS for the explorer**

In `apps/review-workbench/src/styles.css`, append:

```css
/* ── Utility classes ── */
.text-dim { color: var(--text-dim); }

/* ── Data Explorer ── */
.explorer-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 1rem;
}
.explorer-entry {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  color: var(--text-main);
  text-decoration: none;
  transition: background 0.1s;
}
.explorer-entry:hover {
  background: var(--bg-2);
}
.explorer-entry .material-symbols-outlined {
  font-size: 20px;
  color: var(--accent-soft);
}
.explorer-entry-name {
  flex: 1;
  font-family: "JetBrains Mono", "IBM Plex Mono", monospace;
  font-size: 0.875rem;
}
.explorer-entry-meta {
  font-size: 0.75rem;
  color: var(--text-dim);
}
.explorer-preview {
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 1rem;
  font-family: "JetBrains Mono", "IBM Plex Mono", monospace;
  font-size: 0.8rem;
  overflow-x: auto;
  max-height: 70vh;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.explorer-file-view {
  margin-top: 1rem;
}
.explorer-file-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line);
}
```

- [ ] **Step 6: Add explorer link to PortfolioPage**

In `apps/review-workbench/src/pages/PortfolioPage.tsx`, add a link to the explorer in the operator section. After the Review Queue card and before the stats grid, add:

```tsx
<div className="review-queue-card">
  <h2>Data Explorer</h2>
  <p>
    <Link to="/explorer">Browse all local job artifacts</Link> — inspect JSON, Markdown, and screenshots in data/jobs/.
  </p>
</div>
```

- [ ] **Step 7: Verify in browser**

Open http://127.0.0.1:4174/explorer
Expected: directory listing of data/jobs/ root with source folders, clickable tree navigation, file preview for JSON/MD.

- [ ] **Step 8: Commit**

```bash
git add apps/review-workbench/src/pages/DataExplorerPage.tsx \
       apps/review-workbench/src/App.tsx \
       apps/review-workbench/src/api/client.ts \
       apps/review-workbench/src/types/models.ts \
       apps/review-workbench/src/styles.css \
       apps/review-workbench/src/pages/PortfolioPage.tsx
git commit -m "feat(ui): add data explorer for browsing local job artifacts"
```

---

### Task 4: Fix duplicate React key console errors

**Files:**
- Modify: `apps/review-workbench/src/components/GraphCanvas.tsx`

The "Encountered two children with the same key" error comes from ReactFlow receiving nodes with duplicate IDs. The fix belongs in the shared `GraphCanvas` component so all consumers benefit.

- [ ] **Step 1: Deduplicate nodes in GraphCanvas.tsx**

In `apps/review-workbench/src/components/GraphCanvas.tsx`, modify the `toReactFlowNodes` function to filter duplicates:

```typescript
function toReactFlowNodes(graphNodes: GraphNode[], activeNodeIds: string[]): Node[] {
  const activeSet = new Set(activeNodeIds);
  const seen = new Set<string>();
  return graphNodes
    .filter((node) => {
      if (seen.has(node.id)) return false;
      seen.add(node.id);
      return true;
    })
    .map((node, index) => ({
      id: node.id,
      position: {
        x: index === 0 ? 380 : 50 + index * 200,
        y: index === 0 ? 20 : 160,
      },
      data: { label: node.label },
      style: {
        ...DEFAULT_NODE_STYLE,
        ...(activeSet.has(node.id) ? ACTIVE_NODE_STYLE : {}),
      },
    }));
}
```

- [ ] **Step 2: Verify console errors are gone**

Open http://127.0.0.1:4174/jobs/tu_berlin/202362 in browser.
Expected: No "Encountered two children with the same key" warnings in console.

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/components/GraphCanvas.tsx
git commit -m "fix(ui): deduplicate graph node IDs to resolve React key warnings"
```

---

### Task 5: Clean up Portfolio page — separate operator vs developer sections

**Files:**
- Modify: `apps/review-workbench/src/pages/PortfolioPage.tsx`

- [ ] **Step 1: Restructure the page layout**

Rewrite `PortfolioPage.tsx` to separate concerns:

1. **Operator section** (top): Review Queue, Stats, Job list, Data Explorer link
2. **Developer section** (bottom, collapsible): Sandbox links, Boot Sequence, Quick Commands

Move the `dev-path-grid` (workstreams + boot sequence) and operator commands into a collapsible `<details>` element (native HTML toggle, no React state needed):

```tsx
<details className="dev-section">
  <summary>Developer Tools</summary>
  {/* existing dev-path-grid + operator commands */}
</details>
```

- [ ] **Step 2: Verify in browser**

Open http://127.0.0.1:4174/
Expected: Operator content (review queue, stats, jobs, explorer link) appears first. Developer tools collapsed by default.

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/pages/PortfolioPage.tsx
git commit -m "refactor(ui): separate operator and developer sections in portfolio page"
```
