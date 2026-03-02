# Base Profile Data Snapshot

This folder stores imported source data used to enrich `docs/PROFILE.md`.

Purpose:
- keep a local, versioned seed dataset inside this codebase,
- separate imported base records from generated tracker outputs,
- support reproducible profile/document generation.

## Provenance

- External source root: `/home/jp/buscapega`
- Primary profile seed used: `/home/jp/buscapega/Pega/CV_aleman/Lebenslauf/src/data/user_info2.json`
- Job summary source used for gap analysis: `/home/jp/phd/data/pipelined_data/tu_berlin/summary.csv`

## Files

- `profile_base_data.json`: normalized seed profile dataset imported from buscapega sources.
- `job_summary_gaps.json`: explicit records with missing extracted fields (no values invented).

## Data Integrity Rules

- No fabricated values.
- Unknown values remain `"unknown"` or are omitted.
- Salary values are not inferred or backfilled in this snapshot.
