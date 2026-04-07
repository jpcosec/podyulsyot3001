"""XING C4AI scrape translator — consumes XING_SCRAPE portal intent."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.automation.ariadne.models import ScrapePortalDefinition
from src.automation.motors.crawl4ai.contracts import ScrapeDiscoveryEntry
from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter

XING_SCRAPE = ScrapePortalDefinition(
    source_name="xing",
    base_url="https://www.xing.com",
    supported_params=["job_query", "city", "max_days"],
    job_id_pattern=r"-(\d+)(?:[?#]|$)",
)

_RELATIVE_DATE_RE = re.compile(
    r"(vor\s+\d+\s+(?:minute[n]?|stunde[n]?|tag(?:en)?|woche[n]?|monat(?:en)?)|"
    r"\d+\s+(?:minute|minutes|hour|hours|day|days|week|weeks|month|months)\s+ago|"
    r"heute|gestern|today|yesterday)",
    re.IGNORECASE,
)
_SALARY_RE = re.compile(r"(?:€|eur|salary|gehalt|k\b|\d+\s*[kK])", re.IGNORECASE)
_EMPLOYMENT_RE = re.compile(
    r"(full[- ]?time|part[- ]?time|intern(ship)?|contract|temporary|freelance|"
    r"vollzeit|teilzeit|werkstudent|praktikum|befristet|unbefristet)",
    re.IGNORECASE,
)
_LOCATION_RE = re.compile(
    r"(remote|hybrid|onsite|vor ort|homeoffice|[A-Z][A-Za-z\-]+(?:,\s*[A-Z][A-Za-z\-]+)?)"
)


class XingAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for XING."""

    portal = XING_SCRAPE

    @property
    def source_name(self) -> str:
        """Portal identifier for XING."""
        return self.portal.source_name

    @property
    def supported_params(self) -> list[str]:
        """Search parameters supported by the XING search URL builder."""
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        """Extract the numeric job ID from a XING detail URL using the portal pattern."""
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
        """Build a XING job search URL. Accepts job_query, city, max_days. Maps max_days to XING's numeric date filter (1/7/14/30 days)."""
        query = (kwargs.get("job_query") or "data-scientist").replace(" ", "%20")
        city = (kwargs.get("city") or "berlin").replace(" ", "%20")
        max_days = kwargs.get("max_days")
        age_str = ""
        if max_days:
            if max_days <= 1:
                age_str = "1"
            elif max_days <= 7:
                age_str = "7"
            elif max_days <= 14:
                age_str = "14"
            else:
                age_str = "30"
        url = f"https://www.xing.com/jobs/search?keywords={query}&location={city}"
        if age_str:
            url += f"&date={age_str}"
        return url

    def extract_links(self, crawl_result: Any) -> list[ScrapeDiscoveryEntry]:
        """Return structured XING discovery entries parsed from listing HTML."""
        html = crawl_result.cleaned_html or getattr(crawl_result, "html", "")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        raw_html = getattr(crawl_result, "html", "") or html
        raw_fragment_map = self._fragment_map(BeautifulSoup(raw_html, "html.parser"))
        job_links: list[ScrapeDiscoveryEntry] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = self._normalize_job_url(a["href"])
            if not href:
                continue
            if href in seen:
                continue
            seen.add(href)
            card = self._find_listing_card(a, href)
            texts = self._card_texts(card)
            title = self._pick_title(a, card)
            posted_date = self._pick_posted_date(card, texts)
            salary = self._pick_salary(card, texts)
            employment_type = self._pick_employment_type(card, texts)
            company_name, location = self._pick_company_and_location(
                card,
                texts,
                title=title,
                posted_date=posted_date,
                salary=salary,
                employment_type=employment_type,
            )
            teaser_text = "\n".join(texts) or None
            raw_fragments = raw_fragment_map.get(href, [])
            raw_fragment = raw_fragments.pop(0) if raw_fragments else None
            listing_data = {
                key: value
                for key, value in {
                    "job_title": title,
                    "company_name": company_name,
                    "location": location,
                    "salary": salary,
                    "employment_type": employment_type,
                    "posted_date": posted_date,
                }.items()
                if value
            }
            job_links.append(
                ScrapeDiscoveryEntry(
                    url=href,
                    job_id=self.extract_job_id(href),
                    listing_position=len(job_links),
                    listing_snippet=teaser_text,
                    listing_data=listing_data,
                    listing_link={
                        "href": href,
                        "title": a.get("title"),
                        "aria_label": a.get("aria-label"),
                    },
                    source_metadata={
                        "anchor_title": a.get("title"),
                        "anchor_aria_label": a.get("aria-label"),
                        "listing_texts": texts,
                    },
                    listing_case_html=raw_fragment or str(card),
                    listing_case_cleaned_html=str(card),
                )
            )
        return job_links

    def _normalize_job_url(self, href: str | None) -> str | None:
        if not href:
            return None
        absolute = urljoin(f"{self.portal.base_url}/", href)
        if "xing.com/jobs/" not in absolute:
            return None
        return absolute if re.search(r"-(\d+)(?:[?#]|$)", absolute) else None

    def _find_listing_card(self, anchor, href: str):
        card = anchor
        for parent in anchor.parents:
            if getattr(parent, "name", None) not in {"article", "li", "div", "section"}:
                continue
            matches = [
                self._normalize_job_url(link.get("href"))
                for link in parent.find_all("a", href=True)
            ]
            if matches.count(href) == 1:
                card = parent
                if len(self._card_texts(parent)) > 1:
                    return parent
        return card

    def _fragment_map(self, soup: BeautifulSoup) -> dict[str, list[str]]:
        fragments: dict[str, list[str]] = {}
        for anchor in soup.find_all("a", href=True):
            href = self._normalize_job_url(anchor.get("href"))
            if not href:
                continue
            fragments.setdefault(href, []).append(
                str(self._find_listing_card(anchor, href))
            )
        return fragments

    def _card_texts(self, card) -> list[str]:
        texts: list[str] = []
        seen: set[str] = set()
        for value in card.stripped_strings:
            cleaned = " ".join(value.split())
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            texts.append(cleaned)
        return texts

    def _pick_text(self, card, selectors: tuple[str, ...], matcher=None) -> str | None:
        for selector in selectors:
            for node in card.select(selector):
                text = node.get_text(" ", strip=True)
                if text and (matcher is None or matcher.search(text)):
                    return text
        return None

    def _pick_title(self, anchor, card) -> str | None:
        return self._pick_text(
            card, ("h1", "h2", "h3", "[role='heading']")
        ) or anchor.get_text(" ", strip=True)

    def _pick_posted_date(self, card, texts: list[str]) -> str | None:
        text = self._pick_text(
            card,
            ("time", "[datetime]", "[class*='date']", "[data-testid*='date']"),
            _RELATIVE_DATE_RE,
        )
        if text:
            return text
        return next((value for value in texts if _RELATIVE_DATE_RE.search(value)), None)

    def _pick_salary(self, card, texts: list[str]) -> str | None:
        text = self._pick_text(
            card,
            ("[class*='salary']", "[class*='compensation']", "[data-testid*='salary']"),
            _SALARY_RE,
        )
        if text:
            return text
        return next((value for value in texts if _SALARY_RE.search(value)), None)

    def _pick_employment_type(self, card, texts: list[str]) -> str | None:
        text = self._pick_text(
            card,
            (
                "[class*='employment']",
                "[class*='contract']",
                "[data-testid*='employment']",
            ),
            _EMPLOYMENT_RE,
        )
        if text:
            return text
        return next((value for value in texts if _EMPLOYMENT_RE.search(value)), None)

    def _pick_company_and_location(
        self,
        card,
        texts: list[str],
        *,
        title: str | None,
        posted_date: str | None,
        salary: str | None,
        employment_type: str | None,
    ) -> tuple[str | None, str | None]:
        company = self._pick_text(
            card,
            ("[class*='company']", "[data-testid*='company']", "[data-qa*='company']"),
        )
        location = self._pick_text(
            card,
            (
                "[class*='location']",
                "[data-testid*='location']",
                "[data-qa*='location']",
            ),
            _LOCATION_RE,
        )
        reserved = {
            value
            for value in (
                title,
                company,
                location,
                posted_date,
                salary,
                employment_type,
            )
            if value
        }
        candidates = [
            value
            for value in texts
            if value not in reserved
            and not value.startswith("http")
            and len(value) <= 80
        ]
        if company is None and candidates:
            company = candidates[0]
        if location is None:
            location = next(
                (
                    value
                    for value in [*candidates[1:], *candidates[:1]]
                    if _LOCATION_RE.search(value) and value != company
                ),
                None,
            )
        return company, location

    def get_llm_instructions(self) -> str:
        """LLM extraction hints for XING job detail pages."""
        return (
            "Extract from xing.com. Job title is in the <h1>. "
            "Salary and remote policy may appear in a facts sidebar. "
            "Detect the primary language and return its ISO 639-1 code."
        )
