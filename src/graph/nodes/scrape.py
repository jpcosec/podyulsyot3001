"""Backward-compatible shim for the renamed ingest node."""

from src.graph.nodes.ingest import make_ingest_node as make_scrape_node

__all__ = ["make_scrape_node"]
