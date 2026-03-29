"""Render package organized around requests, coordinators, and adapters."""

# TODO(future): fix and stabilize the public render package imports to match the real package layout — see future_docs/issues/standards_alignment_followups.md
from src.render.coordinator import RenderCoordinator
from src.render.request import RenderRequest

__all__ = ["RenderCoordinator", "RenderRequest"]
