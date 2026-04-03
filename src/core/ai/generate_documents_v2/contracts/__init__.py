"""Contract models shared across generate_documents_v2 stages."""

from src.core.ai.generate_documents_v2.contracts.assembly import (
    FinalMarkdownBundle,
    MarkdownDocument,
)
from src.core.ai.generate_documents_v2.contracts.base import IdeaFact, TextAnchor
from src.core.ai.generate_documents_v2.contracts.blueprint import (
    GlobalBlueprint,
    SectionBlueprint,
)
from src.core.ai.generate_documents_v2.contracts.drafting import (
    DraftedDocument,
    DraftedSection,
)
from src.core.ai.generate_documents_v2.contracts.hitl import GraphPatch
from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import (
    EvidenceEdge,
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)

__all__ = [
    "TextAnchor",
    "IdeaFact",
    "ProfileEntry",
    "EvidenceEdge",
    "ProfileKG",
    "SectionMappingItem",
    "JobRequirement",
    "JobLogistics",
    "CompanyData",
    "JobKG",
    "JobDelta",
    "MatchEdge",
    "SectionBlueprint",
    "GlobalBlueprint",
    "DraftedSection",
    "DraftedDocument",
    "MarkdownDocument",
    "FinalMarkdownBundle",
    "GraphPatch",
]
"""Contract models shared across generate_documents_v2 stages."""
