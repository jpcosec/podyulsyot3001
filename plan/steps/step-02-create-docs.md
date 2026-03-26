# Step 02: Create Updated Documentation

**Context:** After implementation, documentation must match the current repository layout and architecture contracts.

---

## 1. Purpose

- Keep architecture docs and step docs aligned
- Remove broken links
- Publish only docs that match existing folders

---

## 2. Files to update

```
docs/node-editor/
├── README.md                  # Entry point with valid links only
├── architecture_pitfalls.md   # Guardrails and anti-patterns
├── l1-app-layer.md            # L1 details
└── product.md                 # Product intent

plan/
├── README.md
├── GUIDE.md
├── IMPLEMENTATION_ORDER.md
└── steps/README.md
```

---

## 3. Required content updates

- `docs/node-editor/README.md`
  - add "Available now" section
  - mark missing docs as planned instead of linking broken paths
- `plan/README.md` and `plan/GUIDE.md`
  - fix `06_flow_contract.md` path references
- `plan/IMPLEMENTATION_ORDER.md` and `plan/steps/README.md`
  - keep one consistent execution order

---

## 4. Verification

- [ ] No broken links in edited files
- [ ] Step order in `plan/steps/README.md` matches `plan/IMPLEMENTATION_ORDER.md`
- [ ] Legacy docs referenced as legacy, not active implementation source

---

## 5. Next step

`step-03-cleanup-plan.md` - Archive or remove temporary files safely.
