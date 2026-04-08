"""Ariadne Form Analyzer - Semantic field mapping for unknown ATS forms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from src.automation.ariadne.models import AriadneAction, AriadneIntent, AriadneTarget


_SEMANTIC_MAP = {
    "first name": "first_name",
    "given name": "first_name",
    "last name": "last_name",
    "family name": "last_name",
    "surname": "last_name",
    "full name": "full_name",
    "email": "email",
    "e-mail": "email",
    "phone": "phone",
    "mobile": "phone",
    "telephone": "phone",
    "cell": "phone",
    "country code": "phone_country_code",
    "linkedin": "linkedin_url",
    "website": "website_url",
    "portfolio": "portfolio_url",
    "github": "github_url",
    "resume": "cv",
    "cv": "cv",
    "cover letter": "letter",
}

_UNSAFE_LABEL_HINTS = {
    "salary",
    "compensation",
    "expected salary",
    "salary expectation",
    "desired salary",
    "ssn",
    "social security",
    "national id",
    "passport",
    "date of birth",
    "birth date",
    "bank",
    "iban",
    "visa",
    "work authorization",
    "sponsorship",
}

_SUBMIT_TEXT_HINTS = ("submit", "apply", "send", "next", "continue")


def _normalize_label(value: str | None) -> str:
    return " ".join((value or "").lower().split())


@dataclass(frozen=True)
class BrowserOSFieldElement:
    """Normalized BrowserOS snapshot element used by the analyzer."""

    element_id: int
    element_type: str
    text: str


class AnalyzedField(BaseModel):
    """A single fillable field discovered during analysis."""

    id: str
    label: str
    semantic_key: str | None = None
    field_type: str = "text"
    target: AriadneTarget
    required: bool = False
    options: list[str] = Field(default_factory=list)
    value: str | None = None
    review_required: bool = False
    review_reason: str | None = None

    def resolve_action(self) -> AriadneAction | None:
        """Build an Ariadne action for the field when it is safe to do so."""
        if self.review_required:
            return None
        if not self.semantic_key and not self.value:
            return None

        intent = AriadneIntent.FILL
        if self.field_type == "file":
            if self.semantic_key == "letter":
                intent = AriadneIntent.UPLOAD_LETTER
            else:
                intent = AriadneIntent.UPLOAD
        elif self.field_type == "select":
            intent = AriadneIntent.SELECT
        elif self.field_type in {"button", "link"}:
            intent = AriadneIntent.CLICK

        value = self.value
        if self.semantic_key and self.semantic_key not in {"cv", "letter"}:
            value = f"{{{{profile.{self.semantic_key}}}}}"

        return AriadneAction(
            intent=intent,
            target=self.target,
            value=value,
            optional=self.semantic_key == "letter" and not self.required,
        )


class AnalyzedForm(BaseModel):
    """A collection of discovered ATS fields plus review state."""

    fields: list[AnalyzedField] = Field(default_factory=list)
    submit_button: AriadneTarget | None = None

    def review_fields(self) -> list[AnalyzedField]:
        return [field for field in self.fields if field.review_required]

    def requires_review(self) -> bool:
        return bool(self.review_fields())

    def review_summary(self) -> str:
        details = []
        for field in self.review_fields():
            reason = field.review_reason or "manual review required"
            details.append(f"{field.label or field.id}: {reason}")
        return "; ".join(details)

    def to_ariadne_actions(self) -> list[AriadneAction]:
        actions: list[AriadneAction] = []
        for field in self.fields:
            action = field.resolve_action()
            if action is not None:
                actions.append(action)
        return actions


class AriadneFormAnalyzer:
    """Analyzes live page snapshots and maps fields to candidate semantics."""

    def analyze_browseros_snapshot(
        self,
        elements: list[BrowserOSFieldElement],
    ) -> AnalyzedForm:
        form = AnalyzedForm()
        for index, element in enumerate(elements):
            if element.element_type not in {"input", "textarea", "select"}:
                if (
                    element.element_type == "button"
                    and not form.submit_button
                    and self._looks_like_submit(element.text)
                ):
                    form.submit_button = AriadneTarget(text=element.text)
                continue

            label = self._browseros_label(elements, index)
            field = AnalyzedField(
                id=str(element.element_id),
                label=label,
                field_type=self._field_type_from_browseros(element, label),
                target=AriadneTarget(text=element.text or label),
            )
            self._classify_field(field)
            if not field.semantic_key and not field.review_required:
                field.review_required = True
                field.review_reason = "browser snapshot field semantics unknown"
            form.fields.append(field)
        return form

    def analyze_generic_elements(self, elements: list[dict[str, Any]]) -> AnalyzedForm:
        form = AnalyzedForm()
        for index, element in enumerate(elements):
            element_type = element.get("type", "text")
            if element_type in {"input", "textarea", "select", "file"}:
                field = AnalyzedField(
                    id=str(element.get("id", index)),
                    label=element.get("label") or element.get("text") or "",
                    field_type=self._field_type_from_generic(element_type, element),
                    target=AriadneTarget(
                        css=element.get("selector"),
                        text=element.get("text") or element.get("label"),
                    ),
                    required=bool(element.get("required", False)),
                    options=list(element.get("options") or []),
                )
                self._classify_field(field)
                form.fields.append(field)
                continue

            if (
                element_type == "button"
                and not form.submit_button
                and self._looks_like_submit(element.get("text"))
            ):
                form.submit_button = AriadneTarget(
                    css=element.get("selector"),
                    text=element.get("text"),
                )
        return form

    def _browseros_label(
        self,
        elements: list[BrowserOSFieldElement],
        index: int,
    ) -> str:
        for previous in range(index - 1, max(-1, index - 4), -1):
            candidate = elements[previous]
            if candidate.element_type in {"text", "label"} and candidate.text:
                return candidate.text
        return elements[index].text

    def _field_type_from_browseros(
        self,
        element: BrowserOSFieldElement,
        label: str,
    ) -> str:
        if element.element_type == "select":
            return "select"
        lowered_label = _normalize_label(label)
        if any(token in lowered_label for token in ("resume", "cv", "cover letter")):
            return "file"
        return "text"

    def _field_type_from_generic(
        self,
        element_type: str,
        element: dict[str, Any],
    ) -> str:
        if element_type == "file":
            return "file"
        if element_type == "select":
            return "select"
        input_type = _normalize_label(str(element.get("input_type") or ""))
        if input_type == "file":
            return "file"
        return element_type

    def _classify_field(self, field: AnalyzedField) -> None:
        lowered_label = _normalize_label(field.label)
        for hint in _UNSAFE_LABEL_HINTS:
            if hint in lowered_label:
                field.review_required = True
                field.review_reason = f"unsafe field '{hint}'"
                return

        for key, semantic in _SEMANTIC_MAP.items():
            if key in lowered_label:
                field.semantic_key = semantic
                return

        if field.required:
            field.review_required = True
            field.review_reason = "required field semantics unknown"

    def _looks_like_submit(self, text: str | None) -> bool:
        lowered = _normalize_label(text)
        return any(token in lowered for token in _SUBMIT_TEXT_HINTS)
