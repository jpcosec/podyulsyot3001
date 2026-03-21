# Claim Admissibility and Policy

## Status

This is a mixed-status policy note.

### Implemented today

- The current runtime enforces strict review parsing and fail-closed routing around `match` and `review_match`.
- Some claim-governance behavior is implicit in prompts, schemas, and review logic rather than enforced as one centralized policy module.

### Future / target-state

- Claim admissibility classes, evidence compatibility rules, and downstream consumption rules should be enforced more explicitly and consistently.

## Target policy shape

### Claim classes

- `direct`
- `bridging`
- `inadmissible`

### Policy intent

- direct claims need compatible evidence
- bridging claims need limitation-safe phrasing
- inadmissible claims must be blocked downstream

## Current interpretation rule

If this file and current runtime behavior disagree, trust the implemented runtime and treat this file as the target policy boundary.
