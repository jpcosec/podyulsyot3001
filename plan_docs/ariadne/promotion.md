# Ariadne Path Promotion

Date: 2026-04-05
Status: design-only

## Purpose

Define how Ariadne paths mature from raw recordings to production-ready replay
artifacts. Promotion is a quality gate — it ensures paths actually work before
they're used for real applications.

## Promotion lifecycle

```
draft → verified → canonical
```

### Draft

A newly recorded path, produced by the recording pipeline from a BrowserOS Agent
or Human motor session.

**Characteristics:**
- Stored in `data/ariadne/recordings/<session>/`
- May contain errors (mis-correlated elements, missing targets, wrong step boundaries)
- Has never been replayed by a deterministic motor
- May need human review and correction

**How it gets here:**
- Recording pipeline completes (watch → record → process → update)

**What can be done with it:**
- Human review (inspect steps, correct targets, fix normalization errors)
- Edit (modify steps, add missing targets, adjust observe blocks)
- Verification replay (next stage)
- Delete (if the recording is unusable)

### Verified

A draft path that has been successfully replayed by a deterministic motor against
the same portal.

**Characteristics:**
- Stored alongside the draft in `data/ariadne/recordings/<session>/` with updated status
- Proven to work at least once on a real portal page
- May still be portal-version-specific (works today, may break tomorrow)

**How it gets here:**
- Take a draft path
- Compile it via a translator to a deterministic motor (BrowserOS CLI or Crawl4AI)
- Replay against the portal
- If replay completes successfully (all observe blocks pass, all actions execute,
  expected end state reached) → promote to verified

**What can be done with it:**
- Promotion to canonical (operator approval)
- Re-verification (replay again to confirm it still works)
- Rejection (if operator inspects and finds issues despite successful replay)

### Canonical

An operator-approved, production-ready path. This is what deterministic motors
use for real apply runs.

**Characteristics:**
- Stored in packaged traces: `<automation-package>/ariadne/traces/<source>/<flow>/`
- Source-controlled and distributed with the code
- Immutable — updates create a new version, never modify the canonical file
- The default path that motors load for a given source + flow

**How it gets here:**
- Operator explicitly approves a verified path
- Path is copied to the packaged traces directory with status `canonical`
- Version number is assigned (or incremented)

**What can be done with it:**
- Replay by any deterministic motor
- Supersede by a newer canonical version (old version kept for rollback)
- Deprecate (mark as no longer valid, e.g., portal changed)

## Promotion triggers

| Transition | Trigger | Who |
|---|---|---|
| → draft | Recording pipeline completes | Automatic |
| draft → verified | Verification replay succeeds | Automatic (operator initiates) |
| verified → canonical | Operator approves | Manual |
| canonical → deprecated | Replay fails consistently, or operator decides | Manual |

## Verification replay

The key quality gate. A verification replay is a dry-run execution of the path
via a deterministic motor against the live portal.

**Steps:**
1. Load the draft path
2. Select a translator (Crawl4AI or BrowserOS CLI)
3. Compile the path to motor format
4. Execute against the portal in dry-run mode (stop before submit)
5. Check results:
   - All observe blocks passed? (expected elements were present)
   - All actions executed without errors?
   - Dry-run stop point reached?
   - Screenshots match expected visual state? (optional, manual check)
6. If all checks pass → mark as verified
7. If any check fails → remain draft, report failures for human review

**What verification does NOT prove:**
- That the submit step works (dry-run stops before submit)
- That the path will work tomorrow (portals change)
- That the path works on a different motor than the one used for verification

## Deprecation

A canonical path can be deprecated when:
- A replay fails consistently (portal changed)
- The operator manually marks it as outdated
- A newer version is promoted to canonical

Deprecated paths are not deleted — they stay in the packaged traces directory
for audit and rollback. They are excluded from automatic path resolution
(motors won't load them by default).

## Path correction workflow

When a draft path has errors:

1. Human reviews the normalized steps
2. Identifies issues (wrong target text, missing action, bad step boundary)
3. Edits the draft path directly (JSON file or future TUI)
4. Runs verification replay again
5. If it passes → promote to verified

This is expected to be common for first recordings, especially from the Human
motor (CDP event capture is noisier than MCP proxy capture).

## Open questions

1. Should verification replay be mandatory, or can an operator promote directly
   from draft to canonical? (Skipping verification is risky but sometimes the
   operator knows the path is correct from visual inspection.)
2. Should there be a "re-verification" schedule? (e.g., re-replay canonical
   paths weekly to detect portal changes early.)
3. Should promotion be reversible? (Demote a canonical path back to verified
   if it starts failing, instead of deprecating it.)
4. Should verification replay test multiple job postings or just one? (One is
   faster; multiple proves the path generalizes across jobs.)
5. Who stores the verification replay results? Ariadne storage or the motor
   that executed the replay?
