# Canonical Path Registry

**Source of Truth** for all file paths in PhD 2.0. Every path mentioned in documentation must match this registry.

---

## Registry

### Job Data (per application)

| Data Type | Canonical Path | Notes |
|-----------|---------------|-------|
| Raw source text | `data/jobs/<source>/<job_id>/raw/source_text.md` | From scrape |
| Screenshots | `data/jobs/<source>/<job_id>/raw/` | `*.png`, `*.jpg` |
| Translated text | `data/jobs/<source>/<job_id>/translated/source_text.md` | Optional |
| **Extract state** | `data/jobs/<source>/<job_id>/nodes/extract/state.json` | Text Tagger output |
| **Match state** | `data/jobs/<source>/<job_id>/nodes/match/state.json` | Evidence links |
| **Strategy Delta** | `data/jobs/<source>/<job_id>/nodes/strategy/delta.json` | Document deltas |
| **Drafting docs** | `data/jobs/<source>/<job_id>/nodes/drafting/` | `cv.md`, `cover_letter.md`, `email.md` |
| Review nodes | `data/jobs/<source>/<job_id>/nodes/review/` | Generic review JSONs |
| Feedback | `data/jobs/<source>/<job_id>/feedback/` | Legacy feedback (deprecated) |
| Final output | `data/jobs/<source>/<job_id>/final/` | PDFs, ZIPs |

### Candidate Data (global)

| Data Type | Canonical Path | Notes |
|-----------|---------------|-------|
| CV Profile | `data/master/profile.json` | Structured knowledge graph |
| Evidence Bank | `data/master/evidence/` | Validated proofs |
| Master Templates | `data/master/templates/` | `master_cv.md`, `master_cover_letter.md`, `master_email.md` |
| Learned Filters | `data/master/filters/` | REJECTION rules learned |

---

## Path Resolution Rules

### Rule 1: Single Source per Data Type
Each data type has ONE canonical path. No exceptions.

### Rule 2: ReviewNodes vs Feedback
- **ReviewNodes** (generic, all stages) → `nodes/review/*.json`
- **Legacy feedback** (match-specific) → `feedback/` (DEPRECATED, avoid)

### Rule 3: Evidence Promotion
When a ReviewNode of type `AUGMENTATION` is validated:
1. Store in `nodes/review/<job_id>/augmentation_<id>.json`
2. Aggregator copies to `data/master/evidence/<evidence_id>.json`

### Rule 4: No Cross-Write
```
UI    → writes to → job folder (nodes/review/, nodes/drafting/)
CLI   → writes to → job folder (all)
API   → exposes → job folder (read/write bridge)
LangGraph → writes to → job folder (state.json, proposed/*.md)
```

---

## Conflict Resolution

| Old/Conflicting Path | Correct Path | Reason |
|---------------------|--------------|--------|
| `feedback/` (for new work) | `nodes/review/` | `feedback/` is deprecated |
| `data/jobs/.../review/` | `nodes/review/` | Normalize to `nodes/` prefix |
| `data/master/evidence_bank/` | `data/master/evidence/` | Shorter is better |

---

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| State JSON | `<stage>_state.json` | `extract_state.json` |
| Review Node | `<type>_<timestamp>.json` | `augmentation_20241215_001.json` |
| Delta | `delta.json` | Single delta per job |
| Draft | `<doc_type>.md` | `cv.md`, `cover_letter.md` |

---

## ⚠️ Race Condition Warning

**PROBLEM**: Multiple processes write to same files:
- LangGraph (background)
- UI (via PUT requests)
- CLI (manual operations)

**RULE**: Before any write:
1. Check if another process holds lock (`.<file>.lock`)
2. If locked, wait or abort with error
3. Acquire lock before writing
4. Release lock after write

**IMPLEMENTATION REQUIRED**:
```bash
# Lock file pattern
.<original_file>.lock

# Atomic write pattern
mv /tmp/<file>.<uuid> <destination>
```
