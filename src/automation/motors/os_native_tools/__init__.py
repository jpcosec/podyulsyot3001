"""OS-Native Tools Motor — Direct Desktop & OS automation.

This motor is planned to support non-browser UI automation (e.g., desktop apps,
native system dialogs) that cannot be reached via Playwright or BrowserOS.
"""

from .provider import OSNativeMotorProvider, OSNativeMotorSession

__all__ = ["OSNativeMotorProvider", "OSNativeMotorSession"]
