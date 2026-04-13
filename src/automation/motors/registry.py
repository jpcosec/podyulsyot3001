"""Motor registry for Ariadne browser adapters."""

from typing import Any, Dict, Type

from src.automation.ariadne.core.adapters.browseros import BrowserOSAdapter
from src.automation.ariadne.core.adapters.crawl4ai import Crawl4AIAdapter
from src.automation.ariadne.core.periphery import BrowserAdapter


class MotorRegistry:
    """Handles browser adapter construction for each motor backend."""

    _adapters: Dict[str, Type[BrowserAdapter]] = {
        "browseros": BrowserOSAdapter,
        "crawl4ai": Crawl4AIAdapter,
    }

    @classmethod
    def get_adapter(cls, name: str, **kwargs: Any) -> BrowserAdapter:
        """Return a configured browser adapter instance."""
        adapter_class = cls._adapters.get(name.lower())
        if not adapter_class:
            raise ValueError(f"Unknown motor: {name}")
        return adapter_class(**kwargs)

    @classmethod
    def get_executor(cls, name: str, **kwargs: Any) -> BrowserAdapter:
        """Backward-compatible alias during the adapter migration."""
        return cls.get_adapter(name, **kwargs)
