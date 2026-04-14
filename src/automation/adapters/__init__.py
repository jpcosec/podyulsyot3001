"""adapters — physical I/O implementations of Sensor, Motor, and LLMClient."""

from src.automation.adapters.browser_os import BrowserOSAdapter
from src.automation.adapters.gemini import GeminiClient

__all__ = ["BrowserOSAdapter", "GeminiClient"]
