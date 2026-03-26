# Step 00: Prerequisites (Data Provider, Worker, QA)

**Spec:** SPEC_GRP_001
**Phase:** 0 (Preflight)
**Priority:** BLOCKING

---

## 1. Purpose

- Prevent hidden blockers before implementation starts
- Validate only Step 00 prerequisites needed to start Step 01 safely

## 1.1 Scope guard (Step 00 only)

- Do not require checks against Step 01+ artifacts or snippets
- Do not implement GRP/UI features beyond prerequisite validation

---

## 2. Required checks

1. **Data provider exists**
   - Either `@/mock/client` is implemented and importable
   - Or fetch-based provider endpoints are documented and reachable
2. **Web Worker support is valid**
   - `new Worker(new URL('./elk.worker.ts', import.meta.url))` compiles in current bundler
3. **UI baseline is clear**
   - `UI-001-01` runs before UI-dependent GRP steps
4. **QA strategy is defined**
   - Local verification per step
   - E2E deferred to final validation step

---

## 3. Local verification

- [ ] Typecheck passes after adding/importing data provider
- [ ] Minimal worker smoke build passes
- [ ] No unresolved imports in Step 00-touched modules/doc references

---

## 4. Next step

Run `UI-001-01`, then continue with `GRP-001-01`.
