from __future__ import annotations

import pytest

from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.nodes.localization import run_localization
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


class FakeTranslator:
    def translate_text(
        self,
        text: str,
        target_lang: str = "en",
        source_lang: str = "en",
    ) -> str:
        del source_lang
        return f"[{target_lang}] {text}"


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_localization_passthrough_for_english(store):
    doc = DraftedDocument(doc_type="cv", sections_md={"summary": "Hello"})
    result = run_localization(
        source="demo",
        job_id="1",
        document=doc,
        target_language="en",
        store=store,
    )
    assert result["localized_document"]["sections_md"]["summary"] == "Hello"


def test_localization_translates_sections(store):
    doc = DraftedDocument(doc_type="letter", sections_md={"intro": "Hello"})
    result = run_localization(
        source="demo",
        job_id="2",
        document=doc,
        target_language="de",
        store=store,
        translator=FakeTranslator(),
    )
    assert result["localized_document"]["sections_md"]["intro"] == "[de] Hello"
