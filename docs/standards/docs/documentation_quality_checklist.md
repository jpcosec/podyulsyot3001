# 📋 Documentation Quality Checklist

Use this checklist to evaluate whether a component's documentation meets the standards defined in [`documentation_and_planning_guide.md`](documentation_and_planning_guide.md) and [`future_docs_guide.md`](future_docs_guide.md).

---

## 1. README Completeness

- [ ] A `README.md` exists in the component's root directory.
- [ ] `## 🏗️ Architecture & Features` — describes shape and rationale, links to the authoritative source files.
- [ ] `## ⚙️ Configuration` — all required env vars and setup instructions in code blocks.
- [ ] `## 🚀 CLI / UI / Usage` — describes intent and entry points; points to the argparse/Settings definition in code, not a duplicated argument table.
- [ ] `## 📝 Data Contract` — points to the Pydantic model file; does not restate field names or types.
- [ ] `## 🛠️ How to Add / Extend` — numbered, algorithmic steps for adding new modules or providers.
- [ ] `## 💻 How to Use` — copy-pasteable quickstart.
- [ ] `## 🚑 Troubleshooting` — common errors mapped as "Symptom → Diagnosis → Solution".
- [ ] Emojis are used consistently as structural markers on section headers.
- [ ] `scripts/validate_doc_links.py` passes — no broken file references.

---

## 2. Inline Code Documentation

- [ ] Every public class has a docstring describing its purpose and responsibilities.
- [ ] ABCs list all abstract methods in their class docstring as a developer contract.
- [ ] Every public function and method has a structured docstring with args and return values.
- [ ] Non-obvious logic, business rules, and intentional workarounds have inline comments.
- [ ] Module-level docstring at the top of each file acts as an executive summary.

---

## 3. Pydantic / Schema Documentation

- [ ] Every `Field(...)` has a `description` that is semantic and human-readable.
- [ ] Descriptions for LLM-consumed fields include examples (and dual-language examples where relevant).
- [ ] MANDATORY vs. OPTIONAL fields are distinguished in class-level comments.

---

## 4. Error Contracts

- [ ] Domain-specific custom exceptions are defined at the top of the file (no reliance on bare `Exception`).
- [ ] No errors are swallowed silently — every caught exception is either logged or re-raised with `from e`.
- [ ] Caught errors are logged with `LogTag.WARN` or `LogTag.FAIL` before any recovery is attempted.
- [ ] ABCs expose operational limits (chunk sizes, retry delays, etc.) as `@property` attributes.

---

## 5. Observability Logs #todo(future): the address might be missplaced

- [ ] All log messages use `LogTag` from `src/shared/log_tags.py` — no hand-written emoji strings.
- [ ] `LogTag.LLM` is used only on paths that invoke an LLM — not on deterministic logic.
- [ ] `LogTag.FAST` is used on deterministic paths to make the distinction explicit.
- [ ] No log messages use plain text where a `LogTag` applies.

---

## 6. Future Work

- [ ] All deferred items have a `# TODO(future): ... — see future_docs/<file>.md` inline marker.
- [ ] Every `future_docs/` entry has a `Last reviewed: YYYY-MM-DD` field.
- [ ] No `future_docs/` entry has a `Last reviewed` date older than 6 months without explicit re-evaluation.

---

## 7. Documentation Lifecycle

- [ ] README `Architecture` file links updated when files are renamed or moved.
- [ ] Pydantic `Field.description` updated when a schema field changes meaning or usage.
- [ ] Observability log tags updated when new mechanisms (retries, fallbacks) are added.
- [ ] No documentation describes behaviour that no longer exists in the code.
