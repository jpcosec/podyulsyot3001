from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar, cast

from langsmith import traceable

T = TypeVar("T")


def _is_langsmith_enabled() -> bool:
    from .config import LLMConfig

    return LLMConfig.from_env().langsmith_enabled


def get_tracer() -> "_Tracer":
    from .config import LLMConfig

    cfg = LLMConfig.from_env()
    if not cfg.langsmith_enabled:
        return _NoOpTracer()
    return _LangSmithTracer(cfg)


class _Tracer:
    def trace(self, name: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        raise NotImplementedError


class _NoOpTracer(_Tracer):
    def trace(self, name: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)


class _LangSmithTracer(_Tracer):
    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg

    def trace(self, name: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        traced_func = traceable(name)(func)  # type: ignore[no-untyped-call]
        return cast(T, traced_func(*args, **kwargs))


@contextmanager
def trace_section(name: str, metadata: Optional[dict[str, Any]] = None):
    if not _is_langsmith_enabled():
        yield
        return

    from langsmith.run_helpers import trace

    if metadata:
        with trace(name, metadata=metadata):
            yield
    else:
        with trace(name):
            yield
