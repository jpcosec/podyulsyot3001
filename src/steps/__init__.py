"""Step protocol and registry for legacy step execution.

DEPRECATED: `src.steps` remains importable for targeted/manual step execution,
but the primary orchestration path is moving to `src/graph/`.

Defines the step execution contract (StepResult) and step registry that maps
CLI verbs to step implementations.
"""

from dataclasses import dataclass


@dataclass
class StepResult:
    """Result of a step execution.

    Attributes:
        status: "ok" (completed successfully), "skipped" (already done, force=False),
                or "error" (failed)
        produced: List of relative paths (within job dir) of files created/updated
        comments_found: Count of inline comments read and logged
        message: Human-readable summary (e.g., "Rendered CV to output/cv.pdf")
    """

    status: str
    produced: list[str]
    comments_found: int
    message: str


# Step registry: maps CLI verb to (module_path, function_name)
# Module paths are import strings; function_name is the entry point (typically "run")
STEPS: dict[str, tuple[str, str]] = {
    "ingest": ("src.steps.ingestion", "run"),
    "match": ("src.steps.matching", "run"),
    "match-approve": ("src.steps.matching", "approve"),
    "motivate": ("src.steps.motivation", "run"),
    "tailor-cv": ("src.steps.cv_tailoring", "run"),
    "draft-email": ("src.steps.email_draft", "run"),
    "render": ("src.steps.rendering", "run"),
    "package": ("src.steps.packaging", "run"),
}
