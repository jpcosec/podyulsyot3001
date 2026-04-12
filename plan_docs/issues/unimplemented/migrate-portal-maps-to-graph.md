# Migrate: Portal Maps to AriadneMap Graph

**Explanation:** Following the deletion of the `portals/` directory, we need to re-migrate the legacy linear JSON maps to the new directed graph `AriadneMap` format. This includes StepStone and LinkedIn Easy Apply flows.

**Reference:** 
- `plan_docs/ariadne/recording_and_promotion.md`
- `src/automation/portals/` (To be re-created)

**What to fix:** Restoration of `easy_apply.json` maps for each portal in the new Graph schema.

**How to do it:**
1.  Re-create `src/automation/portals/<portal>/maps/` directories.
2.  Manually (or via script) convert the linear `steps` from legacy backups to `states` and `edges`.
3.  Define `success_states` and `failure_states` for each map.
4.  Verify against the `AriadneMap` Pydantic model.

**Depends on:** `plan_docs/issues/unimplemented/ariadne-graph-data-models.md`
