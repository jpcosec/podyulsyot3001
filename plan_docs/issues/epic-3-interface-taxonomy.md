# EPIC 3: Interface Taxonomy & Capabilities (The Segregation)

**Explanation:** Segregate the "Motor" abstraction into specialized, primitive JIT interfaces: Executors, Planners, and Capabilities.

**Tasks:**
1.  **Refactor Motor Protocol**: Replace `motor_protocol.py` with segregated `BaseExecutor` (primitives only) and `BasePlanner` (agentic) protocols.
2.  **JIT Translator**: Implement the JIT Translator that compiles exactly one `AriadneIntent` into a motor-specific `MotorCommand` at the moment of execution.
3.  **Link Hinting (Set-of-Mark)**: Implement the Hinting capability to inject alphanumeric overlays on the DOM for hallucination-free LLM navigation.
4.  **Vision Capability**: Refactor Vision from a motor to a stateless utility used by Executors/Planners.

**Success Criteria:**
- Motors no longer receive domain objects (`AriadneStep`), only primitive commands (click x,y).
- The LLM Agent interacts with the UI via simple Hint IDs (e.g., 'AA') instead of complex CSS.

**Depends on:** `epic-2-data-layer-modes.md`
