"""BrowserOS Agent Motor — Autonomous BrowserOS Control.

This motor is planned to support agentic control of BrowserOS, where the agent
makes decisions and executes tool calls directly on the browser instance rather
than following a rigid path defined by a Replayer.
"""

from .provider import BrowserOSAgentMotorProvider, BrowserOSAgentMotorSession

__all__ = ["BrowserOSAgentMotorProvider", "BrowserOSAgentMotorSession"]
