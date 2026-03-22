# Context Router: Dimensions, Pseudocode, and MCP Protocol

## 1. Orthogonal Dimensions Architecture

The repository is treated as a **3D Matrix** where information lives at exact coordinates. The agent only requests coordinates, the system assembles files.

### Axes

| Axis | Name | Values |
|------|------|--------|
| **X** | Technical Domain | `ui`, `api`, `pipeline`, `core`, `data`, `policy` |
| **Y** | Pipeline Stage | `scrape`, `translate`, `extract`, `match`, `strategy`, `drafting`, `render`, `package` |
| **Z** | Resolution Layer | `docs`, `code` |
| **W** | Temporal State | `runtime` (current docs), `plan` (future designs) |

### Domain (Axis X)

| Domain | Description |
|--------|-------------|
| `ui` | React frontend, components, view specifications, graph editing |
| `api` | FastAPI endpoints, network contracts, Pydantic models |
| `pipeline` | LangGraph logic, node flows, semantic gates, transitions |
| `core` | Deterministic functions, local I/O, parsing, PDF rendering |
| `data` | Local-first structure, JSON schemas, Evidence Tree |
| `policy` | Business rules, ethics, usage limits |

### Stage (Axis Y)

```
scrape → translate → extract → match → strategy → drafting → render → package
```

### Content Nature (Sub-axis)

| Nature | Description |
|--------|-------------|
| `philosophy` | Why it exists, intention, design |
| `implementation` | How it's technically implemented |
| `development` | Guides for developing/extending |
| `testing` | Tests, verifications, contracts |
| `expected_behavior` | Observable behavior, edge cases |

---

## 2. Source Code Mapping

### Folder Mapping (Physical Boundaries)

| Domain | Base Folder |
|--------|------------|
| `ui` | `apps/review-workbench/src/` |
| `api` | `src/interfaces/api/` |
| `pipeline` | `src/nodes/`, `src/graph.py` |
| `core` | `src/core/` |
| `data` | `src/core/io/`, `src/interfaces/api/models.py` |

---

## 3. Deterministic Compiler

### ContextRouter Class

```python
# src/tools/context_router.py

import json
import glob
from pathlib import Path
from typing import Optional

class ContextRouter:
    def __init__(self, matrix_path: str = "docs/index/routing_matrix.json"):
        self.matrix = self._load_matrix(matrix_path)
        self.base_path = Path(".")
        
    def _load_matrix(self, path: str) -> list[dict]:
        """Load the routing matrix."""
        with open(path) as f:
            return json.load(f).get("matrix", [])
    
    def _read_file(self, path: str) -> str:
        """Safe file reading."""
        try:
            full_path = self.base_path / path
            return full_path.read_text()
        except FileNotFoundError:
            return f"[FILE NOT FOUND: {path}]"
    
    def _resolve_glob(self, pattern: str) -> list[str]:
        """Resolve glob patterns to real files."""
        return glob.glob(pattern, recursive=True)
    
    def fetch_context(
        self,
        domain: Optional[str] = None,
        stage: Optional[str] = None,
        state: str = "runtime",
        include_code: bool = False,
        nature: Optional[str] = None
    ) -> str:
        """
        Deterministic tool to retrieve context.
        Acts as MCP endpoint for the AI Agent.
        """
        parts = [f"# CONTEXT | domain={domain or 'ALL'} | stage={stage or 'ALL'} | state={state}"]
        
        # 1. Filter by orthogonal coordinates
        entries = []
        for entry in self.matrix:
            if domain and entry.get("domain") != domain:
                continue
            if stage and entry.get("stage") != stage:
                continue
            if nature and entry.get("nature") != nature:
                continue
            doc_path = entry.get("doc_path", "")
            if state == "runtime" and doc_path.startswith("plan/"):
                continue
            if state == "plan" and not doc_path.startswith("plan/"):
                continue
            entries.append(entry)
        
        if not entries:
            return f"# EMPTY | No documents for domain={domain}, stage={stage}, state={state}"
        
        # 2. Assemble Documentation
        parts.append("\n## DOCUMENTATION\n")
        for entry in entries:
            doc_path = entry.get("doc_path")
            if doc_path:
                parts.append(f"\n### FILE: {doc_path}\n```markdown\n{self._read_file(doc_path)}\n```")
        
        # 3. Assemble Source Code
        if include_code:
            parts.append("\n## SOURCE CODE\n")
            for entry in entries:
                for pattern in entry.get("target_code", []):
                    for file_path in self._resolve_glob(pattern):
                        ext = file_path.split('.')[-1]
                        parts.append(f"\n### FILE: {file_path}\n```{ext}\n{self._read_file(file_path)}\n```")
        
        return "\n".join(parts)
```

---

## 4. DocMutator: Real File I/O

### ⚠️ CRITICAL: This class WRITES to disk

Unlike ContextRouter (read-only), DocMutator modifies the filesystem. Use with caution.

```python
# src/tools/doc_mutator.py

import json
import shutil
from pathlib import Path
from typing import Optional, Dict
from context_router import ContextRouter

class DocMutator:
    """Tools for mutating documentation and code with REAL I/O."""
    
    def __init__(self, router: ContextRouter):
        self.router = router
        self.base_path = Path(".")
    
    def _write_file(self, path: str, content: str) -> bool:
        """Write content to file. Creates directories if needed."""
        try:
            file_path = self.base_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return True
        except Exception as e:
            print(f"ERROR writing {path}: {e}")
            return False
    
    def _delete_file(self, path: str) -> bool:
        """Delete a file. Does not fail if missing."""
        try:
            file_path = self.base_path / path
            file_path.unlink(missing_ok=True)
            return True
        except Exception as e:
            print(f"ERROR deleting {path}: {e}")
            return False
    
    def _acquire_lock(self, file_path: str) -> Optional[str]:
        """
        Acquire lock for race condition protection using ATOMIC exclusive create.
        Returns lock_path if acquired, None if already locked (atomic op prevents TOCTOU).
        """
        lock_path = f".{file_path}.lock"
        lock_file = self.base_path / lock_path
        try:
            # 'x' mode = exclusive create, fails if file exists (atomic)
            lock_file.open('x').close()
            return lock_path
        except FileExistsError:
            return None
    
    def _release_lock(self, lock_path: str) -> None:
        """Release lock atomically."""
        try:
            (self.base_path / lock_path).unlink(missing_ok=True)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW A: Sync Code → Docs
    # ─────────────────────────────────────────────────────────────
    
    def sync_code_to_docs(
        self,
        domain: str,
        stage: str,
        generated_docs: Dict[str, str]
    ) -> str:
        """
        Sync documentation to reflect current code state.
        
        Args:
            domain: Technical domain
            stage: Pipeline stage
            generated_docs: Dict of {doc_path: content} to write
        """
        results = []
        
        for doc_path, content in generated_docs.items():
            # Acquire lock to prevent race conditions
            lock_path = self._acquire_lock(doc_path)
            if lock_path is None:
                results.append(f"SKIPPED (locked): {doc_path}")
                continue
            
            if self._write_file(doc_path, content):
                results.append(f"UPDATED: {doc_path}")
            else:
                results.append(f"FAILED: {doc_path}")
            
            self._release_lock(lock_path)
        
        return "\n".join(results)
    
    # ─────────────────────────────────────────────────────────────
    # WORKFLOW B: Implement Plan → Code → Docs
    # ─────────────────────────────────────────────────────────────
    
    def implement_plan(
        self,
        domain: str,
        stage: str,
        plan_doc: str,
        generated_code: Dict[str, str],
        generated_docs: Dict[str, str]
    ) -> str:
        """
        Implement a plan: write code, update docs, delete plan.
        
        Args:
            domain: Technical domain
            stage: Pipeline stage
            plan_doc: Path to plan file to delete after implementation
            generated_code: Dict of {file_path: content}
            generated_docs: Dict of {doc_path: content}
        """
        results = []
        
        # 1. Write code files
        for file_path, content in generated_code.items():
            lock_path = self._acquire_lock(file_path)
            if lock_path is None:
                results.append(f"LOCKED (aborted): {file_path}")
                continue
            
            if self._write_file(file_path, content):
                results.append(f"CREATED/MODIFIED: {file_path}")
            else:
                results.append(f"FAILED: {file_path}")
            
            self._release_lock(lock_path)
        
        # 2. Write docs
        for doc_path, content in generated_docs.items():
            lock_path = self._acquire_lock(doc_path)
            if lock_path is None:
                results.append(f"LOCKED (skipped): {doc_path}")
                continue
            
            if self._write_file(doc_path, content):
                results.append(f"PROMOTED TO RUNTIME: {doc_path}")
            
            self._release_lock(lock_path)
        
        # 3. Delete plan (CRITICAL: prevents orphaned plans)
        if self._delete_file(plan_doc):
            results.append(f"ARCHIVED: {plan_doc}")
        else:
            results.append(f"WARNING: Could not delete {plan_doc}")
        
        return "\n".join(results)
    
    # ─────────────────────────────────────────────────────────────
    # WORKFLOW C: Draft Plan (Runtime → Plan)
    # ─────────────────────────────────────────────────────────────
    
    def draft_plan(
        self,
        domain: str,
        stage: str,
        plan_filename: str,
        plan_content: str
    ) -> str:
        """
        Create a new plan document.
        
        Args:
            domain: Technical domain
            stage: Pipeline stage
            plan_filename: Name of the plan file
            plan_content: Full plan content
        """
        plan_path = f"plan/{domain}/{plan_filename}"
        
        if self._write_file(plan_path, plan_content):
            return f"CREATED: {plan_path}"
        else:
            return f"FAILED: {plan_path}"
    
    # ─────────────────────────────────────────────────────────────
    # WORKFLOW D: Hotfix (Code → Code + Docs)
    # ─────────────────────────────────────────────────────────────
    
    def hotfix(
        self,
        domain: str,
        stage: str,
        fixed_code: Dict[str, str],
        updated_docs: Dict[str, str],
        skip_docs: bool = False
    ) -> str:
        """
        Apply a hotfix to code and optionally update docs.
        
        Args:
            domain: Technical domain
            stage: Pipeline stage
            fixed_code: Dict of {file_path: patched_content}
            updated_docs: Dict of {doc_path: updated_content}
            skip_docs: If True, skip doc update (creates 24h debt)
        """
        results = []
        
        # 1. Fix code
        for file_path, content in fixed_code.items():
            lock_path = self._acquire_lock(file_path)
            if lock_path is None:
                results.append(f"LOCKED (aborted): {file_path}")
                continue
            
            if self._write_file(file_path, content):
                results.append(f"FIXED: {file_path}")
            else:
                results.append(f"FAILED: {file_path}")
            
            self._release_lock(lock_path)
        
        # 2. Update docs (unless --skip-docs)
        if skip_docs:
            results.append("⚠️  DOCS SKIPPED (--skip-docs flag). Run sync within 24h!")
        else:
            for doc_path, content in updated_docs.items():
                lock_path = self._acquire_lock(doc_path)
                if lock_path is None:
                    results.append(f"LOCKED (skipped): {doc_path}")
                    continue
                
                if self._write_file(doc_path, content):
                    results.append(f"DOCS UPDATED: {doc_path}")
                
                self._release_lock(lock_path)
        
        return "\n".join(results)
```

---

## 5. MCP Protocol: Complete Cycle

### System Prompt for Agent

```
You are "PhD 2.0 Architect", an autonomous developer agent.

Your environment is controlled by an Orthogonal Context Matrix.
NEVER guess code structure. ALWAYS use context_router.

AVAILABLE TOOLS:
- fetch_context(domain?, stage?, state?, include_code?, nature?) → string
- sync_code_to_docs(domain, stage, generated_docs) → string
- implement_plan(domain, stage, plan_doc, generated_code, generated_docs) → string
- draft_plan(domain, stage, plan_filename, plan_content) → string
- hotfix(domain, stage, fixed_code, updated_docs, skip_docs?) → string

DOMAINS: ui, api, pipeline, core, data, policy
STAGES: scrape, translate, extract, match, strategy, drafting, render, package
STATE: runtime (current docs), plan (future designs)
NATURES: philosophy, implementation, development, testing, expected_behavior

RULES:
- ALWAYS acquire lock before writing
- hotfix REQUIRES doc update unless --skip-docs
- implement_plan DELETES the plan after success
- draft_plan writes ONLY to plan/ directory
```

### Work Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER/PROMPT                                  │
│  "Implement the Strategy UI plan"                                │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. INTERCEPT: Identify coordinates                              │
│    domain="ui", stage="strategy", intent="implement"            │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DECIDE WORKFLOW                                              │
│    → implement_plan(domain="ui", stage="strategy", ...)         │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. GATHER: fetch_context with coordinates                       │
│    → Read plan/ + runtime + code (if include_code=True)         │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. EXECUTE: Write code, update docs                              │
│    → Acquire locks → Write files → Release locks                │
│    → Delete plan after success                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. RESPOND: Result with confirmation                            │
└─────────────────────────────────────────────────────────────────┘
```

### Prevention Rules

| Mode | Can write code? | Can write docs/runtime? | Can write plan/? | Doc update required? |
|------|-----------------|-------------------------|-------------------|---------------------|
| sync | NO | YES (overwrite) | NO | YES |
| implement | YES | YES (promote) | NO (delete after) | YES |
| design | NO | NO | YES (create) | N/A |
| hotfix | YES | YES (update) | NO | **YES** (unless --skip-docs) |

### Decision Matrix

```
Is there a bug to fix?
├─ YES → hotfix (Workflow D)
│        └─ After fix: MUST update docs (unless --skip-docs)
└─ NO
  ├─ Is there a design document in plan/?
  │   ├─ YES → implement (Workflow B)
  │   └─ NO
  │       ├─ Do you want to propose something new?
  │       │   ├─ YES → design (Workflow C)
  │       │   └─ NO
  │       │       └─ Did code change without updating docs?
  │       │           ├─ YES → sync (Workflow A)
  │       │           └─ NO → STOP (nothing to do)
```
