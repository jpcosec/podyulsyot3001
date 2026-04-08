# OS-Native Tools Motor

**Status: Planned / Conceptual Stub**

This motor is intended to provide automation for non-browser UI components that 
cannot be easily reached or interacted with via web-based automation drivers 
(Crawl4AI/Playwright) or BrowserOS (which focuses on standard web browser DOM).

## Potential Use Cases

- Interacting with native OS file picker dialogs.
- Automating native desktop applications (e.g., custom HR portals).
- Triggering system-level tasks (e.g., certificate installation, OS notifications).

## Protocol Compliance

This package currently provides a `OSNativeMotorProvider` and `OSNativeMotorSession`
that comply with the Ariadne Motor Protocol, but all execution methods raise 
`NotImplementedError`. This allows the Ariadne logic to reference the motor
type without causing runtime failures during discovery.
