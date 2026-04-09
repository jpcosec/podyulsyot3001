from __future__ import annotations

from src.automation.ariadne.job_normalization import (
    hero_markdown_value,
    listing_case_metadata_value,
    merge_rescue_payloads,
    mine_bullets_from_markdown,
    normalize_job_payload,
)


def test_normalize_job_payload_tracks_cleaned_diagnostics() -> None:
    result = normalize_job_payload(
        {"job_title": "Data Scientist", "location": "Berlin + 0 more"},
        markdown_text=(
            "# Data Scientist\n"
            "* Example Research GmbH\n"
            "* [Berlin](https://example.test/location)\n"
            "## Your responsibility\n"
            "Conduct experiments.\n"
            "## Your profile\n"
            "- Python\n"
        ),
    )

    assert result.payload["company_name"] == "Example Research GmbH"
    assert result.payload["location"] == "Berlin"
    assert result.diagnostics["field_sources"]["company_name"] == "hero_markdown"
    assert result.diagnostics["field_sources"]["requirements"] == "text_mining"


def test_merge_rescue_payloads_preserves_existing_scalars() -> None:
    merged = merge_rescue_payloads(
        base_payload={"location": "Berlin", "company_name": "Example Co"},
        rescue_payload={
            "location": "Presencial",
            "company_name": "Be an early applicant",
            "requirements": ["Python"],
        },
    )

    assert merged == {
        "location": "Berlin",
        "company_name": "Example Co",
        "requirements": ["Python"],
    }


def test_listing_case_metadata_value_recovers_xing_company() -> None:
    listing_case = {
        "teaser_title": "Data Scientist",
        "source_metadata": {
            "listing_texts": [
                "Be an early applicant",
                "Data Scientist",
                "Jobriver HR Service",
                "Berlin",
                "+ 0 more",
                "Full-time",
            ]
        },
    }

    assert (
        listing_case_metadata_value(listing_case, field="company_name")
        == "Jobriver HR Service"
    )
    assert listing_case_metadata_value(listing_case, field="location") == "Berlin"


def test_hero_markdown_value_scopes_stepstone_hero_block() -> None:
    markdown = (
        "[](https://www.stepstone.de/de)\n"
        "Suche\n"
        "# Machine Learning Engineer / Data Scientist Google Cloud (all genders)\n"
        "* adesso SE\n"
        "* Berlin, Bremen\n"
        "* Feste Anstellung\n"
        "**Machine Learning Engineer / Data Scientist Google Cloud (all genders)**[ adesso SE](https://example.test/company)\n"
        "adesso steht fur IT-Exzellenz.\n"
    )

    assert hero_markdown_value(markdown, field="company_name") == "adesso SE"
    assert hero_markdown_value(markdown, field="location") == "Berlin, Bremen"


def test_hero_markdown_value_skips_stepstone_contract_metadata_for_location() -> None:
    markdown = (
        "# IT Business Analyst:in Payroll\n"
        "* Deutsche Bahn AG\n"
        "* Berlin, Essen, Frankfurt am Main, Hannover, Nurnberg, Regensburg\n"
        "* Feste Anstellung\n"
        "* Homeoffice moglich, Teilzeit, Vollzeit\n"
    )

    assert (
        hero_markdown_value(markdown, field="location")
        == "Berlin, Essen, Frankfurt am Main, Hannover, Nurnberg, Regensburg"
    )


def test_mine_bullets_from_markdown_supports_xing_headings() -> None:
    bullets = mine_bullets_from_markdown(
        "## **Deine Rolle**\n"
        "- Build secure ML pipelines\n"
        "## Qualifikation\n"
        "**Dein Equipment**\n"
        "- Python\n"
    )

    assert bullets["responsibilities"] == ["Build secure ML pipelines"]
    assert bullets["requirements"] == ["Python"]
