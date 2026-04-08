# Vision Motor

**Status: Planned / Conceptual Stub**

This motor is intended to provide visual-first automation where the system
operates primarily by "seeing" the screen (screenshots, screen recording) 
rather than using DOM/CSS selectors.

## Potential Use Cases

- Portals with obfuscated or highly dynamic DOM structures.
- Interaction with canvas-based web applications.
- Visual validation of layout and content.
- Using LLMs with vision capabilities (e.g., GPT-4V, Claude 3.5 Sonnet) to 
  interpret complex UIs.

## Protocol Compliance

This package currently provides a `VisionMotorProvider` and `VisionMotorSession`
that comply with the Ariadne Motor Protocol, but all execution methods raise 
`NotImplementedError`. This allows the Ariadne logic to reference the motor
type without causing runtime failures during discovery.
