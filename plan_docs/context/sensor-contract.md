---
type: model
domain: scraping
source: src/automation/ariadne/contracts/base.py
---

# Pill: Sensor Contract

## Structure
`Sensor` is the read-only browser perception contract.

Required behavior:
- `async def perceive(self) -> SnapshotResult`
- `async def is_healthy(self) -> bool`

Responsibilities:
- read the current browser reality
- return a normalized snapshot DTO
- avoid mutating browser state while perceiving
- report its own connectivity health

## Usage
`Theseus` and `Delphi` use `Sensor` to inspect the current page before choosing actions.

Anything that clicks, types, or changes the page belongs to `Motor`, not `Sensor`.

## Verify
Check that perception code returns `SnapshotResult` and does not hide action side effects inside read paths.
