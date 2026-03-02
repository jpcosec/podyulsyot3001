"""Motivation letter generation service."""

from .service import (
    EmailDraftResult,
    MotivationGenerationResult,
    MotivationLetterService,
    MotivationPDFResult,
)

__all__ = [
    "MotivationLetterService",
    "MotivationGenerationResult",
    "MotivationPDFResult",
    "EmailDraftResult",
]
