"""Motor Registry — Factory for loading JIT Executors."""

from typing import Dict, Type

from src.automation.ariadne.contracts.base import Executor
from src.automation.motors.browseros.executor import BrowserOSCliExecutor
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


class MotorRegistry:
    """Handles the instantiation of JIT Executors."""

    _executors: Dict[str, Type[Executor]] = {
        "browseros": BrowserOSCliExecutor,
        "crawl4ai": Crawl4AIExecutor,
    }

    @classmethod
    def get_executor(cls, name: str) -> Executor:
        """Returns an instance of the requested executor."""
        executor_class = cls._executors.get(name.lower())
        if not executor_class:
            raise ValueError(f"Unknown executor: {name}")
        return executor_class()
