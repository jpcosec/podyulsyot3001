# Map Concept: Document Labyrinth + AriadneThread Split

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

### 1. Explanation
 AGENTS.md, README.md, and STANDARDS.md must define Ariadne's long-term memory as two cooperating objects: `Labyrinth` (topology — "where am I?") and `AriadneThread` (mission path — "where do I go next?"). Neither is a script or playback trace.

**Reference:** `AGENTS.md`, `README.md`, `STANDARDS.md`

**Status:** Partially wrong. AGENTS.md describes Ariadne's cascade correctly but doesn't explicitly define what a "map" is. New contributors (and agents) arriving from the CLI docs may assume `--portal linkedin` means "play back the linkedin recording".

**Why it matters:** This mental model leak caused the CLI to be designed with `apply` vs `scrape` as separate commands, when both are just the same graph run with different `mission_id`s on the same map. If agents or developers misunderstand this, they'll keep recreating domain-specific wrappers.

**Real fix:**
Add a "Labyrinth & Thread" section to `AGENTS.md` (and/or `STANDARDS.md`) explaining:
- `Labyrinth` is a topological graph of rooms (page states) with predicates that `Theseus` uses to answer "where am I?".
- `AriadneThread` is a mission-specific sequence of transitions ("which step next for `easy_apply`?"). Same labyrinth, different threads per mission.
- The `instruction` / `mission_id` selects which thread is loaded — not a different map file.
- Scraping and applying are the same graph execution with different `AriadneThread` instances over the same `Labyrinth`.
- Both are authored via `Recorder.promote()`, not written by hand.

**Don't:** Document the map as a "script" or "playbook" — these words imply linearity.

**Steps:**
1. Add "What is a Map?" section to `AGENTS.md`.
2. Optionally add a one-paragraph note in `STANDARDS.md` under the architecture section.

### 2. Reference
`ariadne-oop-architecture.md`

### 3. Real fix
Document the split.

### 4. Steps
1. Write documentation.

### 5. Test command
N/A

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Labyrinth Model](../context/labyrinth-model.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Ariadne Thread Model](../context/ariadne-thread-model.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
