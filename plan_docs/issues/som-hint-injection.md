# Set-of-Mark: Hint Injection in Sensor.perceive

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

**Explanation:** The `Sensor` (or a `HintingCapability` injected into `Theseus`) must inject hint labels (`[AA]`, `[AB]`) into the UI before capturing the final screenshot that `Delphi` will consume.

**Reference:** `src/automation/ariadne/core/periphery.py` (`Sensor`), `src/automation/ariadne/core/actors.py` (`Theseus`), `src/automation/ariadne/capabilities/hinting.js`

**Status:** Not started.

### 📦 Required Context Pills
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 3 - DOM Hostility](../context/law-3-dom-hostility.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.
