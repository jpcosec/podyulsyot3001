"""Ariadne 2.0 Core — The cognitive engine of the browser automation.

This package contains the protocols, memory objects, and actors that define
Ariadne's behavior.
"""

from src.automation.ariadne.core.periphery import BrowserAdapter, Motor, Sensor

__all__ = ["Sensor", "Motor", "BrowserAdapter"]
