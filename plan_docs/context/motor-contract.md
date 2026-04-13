---
type: model
domain: scraping
source: src/automation/ariadne/contracts/base.py
---

# Pill: Motor Contract

## Structure
`Motor` is the browser mutation contract.

Required behavior:
- `async def act(self, command: MotorCommand) -> ExecutionResult`
- `async def is_healthy(self) -> bool`

Responsibilities:
- execute primitive browser actions
- return structured execution outcomes
- avoid owning mission or topology logic
- report its own connectivity health

## Usage
`Theseus` and `Delphi` call `Motor` to mutate the world after deciding what to do.

`Motor` executes commands; it does not decide which command should run.

## Verify
Check that browser action code is expressed through `MotorCommand` and returns `ExecutionResult` rather than leaking runtime-specific raw responses upward.
