from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class StepStoneDetailPayload:
    title: str | None
    company: str | None
    location: str | None
    description: str | None
    salary: str | None
    employment_type: str | None
    posted_date: str | None
    apply_button_text: str | None
    apply_button_url: str | None


def is_stepstone_listing_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return "/jobs" in path or path.endswith("/work")


def is_stepstone_detail_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return "stellenangebote--" in path and path.endswith("-inline.html")


def extract_stepstone_listing_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()

    for link in soup.select('a[data-at="job-item-title"]'):
        href = link.get("href")
        if not isinstance(href, str) or not href:
            continue
        absolute = _normalize_url(urljoin(base_url, href))
        if not absolute:
            continue
        if is_stepstone_detail_url(absolute) and absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)

    if urls:
        return urls

    for link in soup.select("a[href]"):
        href = link.get("href")
        if not isinstance(href, str) or not href:
            continue
        absolute = _normalize_url(urljoin(base_url, href))
        if not absolute:
            continue
        if is_stepstone_detail_url(absolute) and absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)
    return urls


def extract_stepstone_detail(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_text(
        soup,
        "h1[data-at='header-job-title'], h1.listing-title, h1.job-ad-display-header-title",
    )
    company = _extract_text(
        soup,
        "a[data-at='header-company-name'], div.company-header-name, a.listing-company-link",
    )
    location = _extract_text(
        soup,
        "span[data-at='header-location'], div.location-display, span.job-ad-display-location",
    )
    description = _extract_text(
        soup,
        "div[data-at='jobad-content'], div.listing-content, div.job-ad-display-content, section.job-description",
        separator="\n",
    )
    salary = _extract_text(
        soup,
        "span[data-at='header-salary'], div.salary-display, span.job-ad-display-salary",
    )
    employment_type = _extract_text(
        soup,
        "span[data-at='header-job-type'], span.employment-type, div.job-type-badge",
    )
    posted_date = _extract_text(
        soup,
        "span[data-at='header-timeago'], time.posted-date, span.job-ad-display-date",
    )
    apply_button = soup.select_one(
        "button[data-at='apply-button'], a.apply-button, button.application-button, a[href*='apply']"
    )
    apply_button_text = apply_button.get_text(strip=True) if apply_button else None
    apply_button_url: str | None = None
    if apply_button is not None:
        href = apply_button.get("href")
        if isinstance(href, str):
            apply_button_url = href

    payload = StepStoneDetailPayload(
        title=title,
        company=company,
        location=location,
        description=description,
        salary=salary,
        employment_type=employment_type,
        posted_date=posted_date,
        apply_button_text=apply_button_text,
        apply_button_url=apply_button_url,
    )
    return {
        "title": payload.title,
        "company": payload.company,
        "location": payload.location,
        "description": payload.description,
        "salary": payload.salary,
        "employment_type": payload.employment_type,
        "posted_date": payload.posted_date,
        "application": {
            "apply_button_text": payload.apply_button_text,
            "apply_button_url": payload.apply_button_url,
        },
        "raw_text": _build_stepstone_raw_text(payload),
    }


def _extract_text(
    soup: BeautifulSoup, selector: str, separator: str = " "
) -> str | None:
    elem = soup.select_one(selector)
    if not elem:
        return None
    text = elem.get_text(separator=separator, strip=True)
    return text if text else None


def _build_stepstone_raw_text(payload: StepStoneDetailPayload) -> str:
    lines: list[str] = []
    if payload.title:
        lines.append(payload.title)
    if payload.company:
        lines.append(payload.company)
    if payload.location:
        lines.append(payload.location)
    if payload.employment_type:
        lines.append(payload.employment_type)
    if payload.posted_date:
        lines.append(payload.posted_date)
    if payload.salary:
        lines.append(f"Salary: {payload.salary}")
    if payload.description:
        lines.append("")
        lines.append(payload.description)
    if payload.apply_button_text:
        lines.append("")
        lines.append(f"Apply: {payload.apply_button_text}")
    return "\n".join(lines).strip()


def _normalize_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    cleaned = parsed._replace(query="", fragment="")
    return urlunparse(cleaned)
