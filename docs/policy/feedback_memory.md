# Feedback Memory (Current Status)

Current implementation status: partial.

## What exists today

- Match review stores round-local feedback artifacts (`feedback.json`) used as regeneration context.
- There is no complete cross-stage reusable feedback memory subsystem yet.

## Planned properties

1. Local correction for the current job.
2. Historical reuse across jobs.
3. Stage-aware targeting.
4. Controlled retrieval policy.

## Implementation gate

Do not mark this complete until feedback persistence and retrieval are implemented and wired into at least one review loop beyond ad-hoc round feedback files.
