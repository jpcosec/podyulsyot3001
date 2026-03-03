"""Pipeline classes split out of src.utils.pipeline."""

from src.graph.pipelines.matching import MatchProposalPipeline
from src.graph.pipelines.tailoring import CVTailoringPipeline

__all__ = ["CVTailoringPipeline", "MatchProposalPipeline"]
