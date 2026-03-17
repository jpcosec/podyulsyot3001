# Feedback Memory Spec

Status: planned, not implemented as a complete cross-stage subsystem.

## Objective

Route reviewer feedback into reusable, stage-aware memory artifacts without polluting control-plane state.

## Planned properties

1. Local correction for current job
2. Historical reuse across jobs
3. Stage-aware targeting
4. Controlled retrieval policy

## Implementation gate

Do not mark complete until feedback persistence and retrieval are implemented and wired into at least one review loop beyond ad-hoc round feedback files.
