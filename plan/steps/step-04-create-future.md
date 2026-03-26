# Step 04: Maintain Future Specs Folder

**Context:** `plan/future/` already exists. This step keeps deferred specs aligned with the current implementation roadmap.

---

## 1. Purpose

- Keep deferred ideas documented without polluting current execution steps
- Ensure `plan/future/README.md` reflects the actual spec files present
- Track only realistic post-v2 features

---

## 2. Current folder

```
plan/future/
├── README.md
├── SPEC_FUTURE_001_performance.md
└── SPEC_FUTURE_002_export.md
```

---

## 3. Action

- Review `plan/future/README.md` and ensure the table matches real files.
- Add new future specs only when a concrete dependency and scope are known.
- Keep each future spec self-contained (`Problem`, `Solution`, `Dependencies`, `Risks`).

---

## 4. Verification

- [ ] `plan/future/README.md` lists only existing spec files
- [ ] No duplicate templates or stale placeholders
- [ ] Priorities still match roadmap assumptions

---

## 5. Next step

`step-05-final-validation.md` - Run consolidated end-to-end validation.
