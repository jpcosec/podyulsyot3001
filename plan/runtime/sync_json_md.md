# sync_json_md (Current Status)

Current implementation status: not implemented as a reusable service module.

Current behavior in code:

- Review markdown and JSON surfaces are generated/parsing logic is embedded in node-specific code paths.
- No centralized `src/core/tools/sync_json_md/` package exists.

Planning/spec details are maintained in:

- `plan/spec/sync_json_md_spec.md`
