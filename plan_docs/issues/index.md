# Automation Issues Index

This file is the entrypoint for subagents deployed to solve automation issues.

All issue-fixing work must stay aligned with the rest of `plan_docs/` and `docs/`, with special care for `docs/standards/` so implementation, tests, and documentation remain consistent with the project's rules.

## Working rule for every issue

Once an issue is solved, the next step is always:

1. Check whether any existing test is no longer valid and delete it if needed.
2. Add new tests where necessary.
3. Run the relevant tests.
4. Update `changelog.md`.
5. Delete the solved issue from both this index and the corresponding file in `plan_docs/issues/`.
6. Make a commit that clearly states what was fixed, making sure all required files are staged.

## Priority roadmap

### Phase 1 — Foundations

1. `plan_docs/issues/gaps/discovery-entry-contract.md`
2. `plan_docs/issues/gaps/trace-normalization-quality.md`
3. `plan_docs/issues/gaps/language-detection-hardening.md`
4. `plan_docs/issues/gaps/crawl4ai-llm-extraction-strategy.md`
5. `plan_docs/issues/gaps/representative-schema-samples.md`
6. `plan_docs/issues/gaps/browseros-domain-interface-boundary.md`
7. `plan_docs/issues/gaps/browseros-letter-upload-routing.md`

### Phase 2 — Built on the foundations

8. `plan_docs/issues/gaps/xing-listing-metadata-composition.md`
   - depends on `plan_docs/issues/gaps/discovery-entry-contract.md`
9. `plan_docs/issues/gaps/end-to-end-apply-coverage.md`
10. `plan_docs/issues/gaps/cross-motor-applymeta-consistency.md`
   - depends on `plan_docs/issues/gaps/end-to-end-apply-coverage.md`

### Phase 3 — Routing and apply enablement

11. `plan_docs/issues/unimplemented/application-routing-enrichment.md`
12. `plan_docs/issues/unimplemented/portal-routing-layer.md`
   - depends on `plan_docs/issues/unimplemented/application-routing-enrichment.md`
13. `plan_docs/issues/unimplemented/cross-portal-discovery.md`
   - depends on `plan_docs/issues/unimplemented/application-routing-enrichment.md`

### Phase 4 — Human loop, safety, and fallback execution

14. `plan_docs/issues/unimplemented/apply-hitl-channel.md`
15. `plan_docs/issues/unimplemented/credential-store.md`
16. `plan_docs/issues/unimplemented/anti-bot-danger-detection.md`
   - depends on `plan_docs/issues/unimplemented/apply-hitl-channel.md`
17. `plan_docs/issues/unimplemented/openbrowser-level2-integration.md`
   - depends on `plan_docs/issues/unimplemented/credential-store.md`
   - depends on `plan_docs/issues/unimplemented/apply-hitl-channel.md`

### Phase 5 — Higher-level capability

18. `plan_docs/issues/unimplemented/ats-form-analyzer.md`
19. `plan_docs/issues/unimplemented/conceptual-motors.md`
   - no blocking dependency; lower urgency unless roadmap scaffolding is needed

## Dependency summary

- `plan_docs/issues/gaps/xing-listing-metadata-composition.md` -> `plan_docs/issues/gaps/discovery-entry-contract.md`
- `plan_docs/issues/gaps/cross-motor-applymeta-consistency.md` -> `plan_docs/issues/gaps/end-to-end-apply-coverage.md`
- `plan_docs/issues/unimplemented/portal-routing-layer.md` -> `plan_docs/issues/unimplemented/application-routing-enrichment.md`
- `plan_docs/issues/unimplemented/cross-portal-discovery.md` -> `plan_docs/issues/unimplemented/application-routing-enrichment.md`
- `plan_docs/issues/unimplemented/openbrowser-level2-integration.md` -> `plan_docs/issues/unimplemented/credential-store.md`
- `plan_docs/issues/unimplemented/openbrowser-level2-integration.md` -> `plan_docs/issues/unimplemented/apply-hitl-channel.md`
- `plan_docs/issues/unimplemented/anti-bot-danger-detection.md` -> `plan_docs/issues/unimplemented/apply-hitl-channel.md`
